from __future__ import unicode_literals

from django.middleware.csrf import rotate_token, CsrfViewMiddleware
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist

from is_core.auth_token.models import Token, AnonymousToken
from is_core import config
from is_core.patterns import is_rest_request
from is_core.utils import header_name_to_django


def login(request, user, expiration=True):
    """
    Persist token into database. Token is stored inside cookie therefore is not necessary
    reauthenticate user for every request.
    """
    if user is None:
        user = request.user
    token = Token.objects.create(user=user, user_agent=request.META.get('HTTP_USER_AGENT', '')[:256],
                                 expiration=expiration)
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
    if hasattr(user, 'is_authenticated') and not user.is_authenticated():
        user = None
    user_logged_out.send(sender=user.__class__, request=request, user=user)

    if hasattr(request, 'user'):
        request.user = AnonymousUser()

    if hasattr(request, 'token') and request.token.is_active:
        token = request.token
        token.is_active = False
        token.save()


def get_token(request):
    """
    Returns the token model instance associated with the given request token key.
    If no user is retrieved AnonymousToken is returned.
    """

    auth_token = (request.META.get(header_name_to_django(config.IS_CORE_AUTH_HEADER_NAME)) or 
                  request.COOKIES.get(config.IS_CORE_AUTH_COOKIE_NAME))

    try:
        token = Token.objects.get(key=auth_token, is_active=True)
        if not token.is_expired:
            if auth_token == request.META.get(header_name_to_django(config.IS_CORE_AUTH_HEADER_NAME)):
                token.is_from_header = True
            return token
    except ObjectDoesNotExist:
        pass
    return AnonymousToken()


def dont_enforce_csrf_checks(request):
    return (getattr(request, '_dont_enforce_csrf_checks', False) or
            (request.META.get(header_name_to_django(config.IS_CORE_AUTH_HEADER_NAME)) and is_rest_request(request)))


def get_user(request):
    """
    Returns the user model instance associated with the given request token.
    If no user is retrieved an instance of `AnonymousUser` is returned.
    """
    if hasattr(request, 'token'):
        user_id = request.token.user.pk
        user = ModelBackend().get_user(user_id) or AnonymousUser()
    else:
        user = AnonymousUser()
    return user
