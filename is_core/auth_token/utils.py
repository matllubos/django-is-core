import re

from django.middleware.csrf import rotate_token
from django.contrib.auth import load_backend
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.models import AnonymousUser
from django.conf import settings as django_settings

from ipware.ip import get_ip

from is_core.config import settings
from is_core.auth_token.models import Token, AnonymousToken
from is_core.utils import header_name_to_django
from is_core.utils.compatibility import _get_backends


def login(request, user, expiration=True, auth_slug=None, related_objs=None, backend=None):
    """
    Persist token into database. Token is stored inside cookie therefore is not necessary
    reauthenticate user for every request.
    """
    related_objs = related_objs if related_objs is not None else ()

    if user is None:
        user = request.user

    try:
        backend = backend or user.backend
    except AttributeError:
        backends = _get_backends(return_tuples=True)
        if len(backends) == 1:
            _, backend = backends[0]
        else:
            raise ValueError(
                'You have multiple authentication backends configured and '
                'therefore must provide the `backend` argument or set the '
                '`backend` attribute on the user.'
            )

    token = Token.objects.create(user=user, user_agent=request.META.get('HTTP_USER_AGENT', '')[:256],
                                 expiration=expiration, auth_slug=auth_slug, ip=get_ip(request),
                                 backend=backend)

    for related_obj in related_objs:
        token.related_objects.create(content_object=related_obj)
    if hasattr(request, 'user'):
        request.user = user
    request.token = token
    rotate_token(request)
    user_logged_in.send(sender=user.__class__, request=request, user=user)


def logout(request):
    """
    Set current token to inactive.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, 'user', None)
    if hasattr(user, 'is_authenticated') and not user.is_authenticated:
        user = None
    user_logged_out.send(sender=user.__class__, request=request, user=user)

    if hasattr(request, 'token') and request.token.is_active:
        if request.token.active_takeover:
            active_takeover = request.token.active_takeover
            active_takeover.is_active = False
            active_takeover.save()

            if hasattr(request, 'user'):
                request.user = request.token.user
        else:
            token = request.token
            token.is_active = False
            token.save()

            if hasattr(request, 'user'):
                request.user = AnonymousUser()


def create_auth_header_value(token):
    """
    Returns a value for request "Authorization" header with the token.
    """
    return '{} {}'.format(settings.AUTH_HEADER_TOKEN_TYPE, token)


def parse_auth_header_value(request):
    """
    Returns a token parsed from the "Authorization" header.
    """
    match = re.match(
        '{} ([^ ]+)$'.format(settings.AUTH_HEADER_TOKEN_TYPE),
        request.META.get(header_name_to_django(settings.AUTH_HEADER_NAME), '')
    )
    return match.group(1) if match else None


def get_token(request):
    """
    Returns the token model instance associated with the given request token key.
    If no user is retrieved AnonymousToken is returned.
    """
    auth_token = parse_auth_header_value(request) or request.COOKIES.get(settings.AUTH_COOKIE_NAME)

    try:
        token = Token.objects.get(key=auth_token, is_active=True)
        if not token.is_expired:
            if auth_token == request.META.get(header_name_to_django(settings.AUTH_HEADER_NAME)):
                token.is_from_header = True
            return token
    except Token.DoesNotExist:
        pass
    return AnonymousToken()


def dont_enforce_csrf_checks(request):
    return (getattr(request, '_dont_enforce_csrf_checks', False) or parse_auth_header_value(request))


def get_user_from_token(token):
    if token:
        backend_path = token.backend
        if backend_path in django_settings.AUTHENTICATION_BACKENDS:
            active_takeover_id = token.active_takeover.user.pk if token.active_takeover else None
            user_id = token.user.pk
            backend = load_backend(backend_path)
            return backend.get_user(active_takeover_id) or backend.get_user(user_id) or AnonymousUser()
    return AnonymousUser()


def get_user(request):
    """
    Returns the user model instance associated with the given request token.
    If no user is retrieved an instance of `AnonymousUser` is returned.
    """
    return get_user_from_token(getattr(request, 'token'))


def takeover(request, user):
    if request.user == user:
        return False
    else:
        request.token.user_takeovers.update(is_active=False)
        request.token.user_takeovers.create(user=user, is_active=True)
        return True
