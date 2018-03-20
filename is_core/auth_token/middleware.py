import time

from django.utils.encoding import force_text
from django.utils.functional import SimpleLazyObject
from django.utils.http import cookie_date

from is_core.auth_token import utils
from is_core.config import settings
from is_core.utils import header_name_to_django
from is_core.utils.compatibility import MiddlewareMixin


def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = utils.get_user(request)
    return request._cached_user


class TokenAuthenticationMiddlewares(MiddlewareMixin):

    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = utils.get_token(request)
        request.user = SimpleLazyObject(lambda: get_user(request))
        request._dont_enforce_csrf_checks = utils.dont_enforce_csrf_checks(request)

    def _update_token_and_cookie(self, request, response, max_age, expires):
        request.token.save()
        response.set_cookie(settings.AUTH_COOKIE_NAME, force_text(request.token.key), max_age=max_age,
                            expires=expires, httponly=settings.AUTH_COOKIE_HTTPONLY,
                            secure=settings.AUTH_COOKIE_SECURE, domain=settings.AUTH_COOKIE_DOMAIN)
        return response

    def _set_auth_expiration_header(self, request, response):
        response[settings.AUTH_TOKEN_EXPIRATION_HEADER] = request.token.str_time_to_expiration

    def _is_token_renewal_exempt(self, request):
        return (getattr(request, 'auth_token_renewal_exempt', False) or
                header_name_to_django(settings.AUTH_TOKEN_RENEWAL_EXEMPT_HEADER) in request.META)

    def process_response(self, request, response):
        """
        Set cookie with token key if user is authenticated
        """
        # Save the session data and refresh the client cookie.
        # Skip session save for 500 responses, refs #3881.
        if response.status_code != 500 and hasattr(request, 'token') and request.token.is_active:
            if request.token.expiration:
                # The user did not choose to be permanently signed. Hence, the authentication cookie that holds the
                # token value is set to expire when the browser is closed
                max_age = None
                expires = None
            else:
                max_age = settings.AUTH_COOKIE_AGE
                expires = cookie_date(time.time() + max_age)

            if not self._is_token_renewal_exempt(request):
                self._update_token_and_cookie(request, response, max_age, expires)

            self._set_auth_expiration_header(request, response)

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.auth_token_renewal_exempt = getattr(view_func, 'auth_token_renewal_exempt', False)
