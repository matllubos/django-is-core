from django.utils.functional import SimpleLazyObject

from is_core import config, auth_token
from django.contrib.sessions.middleware import SessionMiddleware
import time
from django.utils.http import cookie_date

SessionMiddleware

def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = auth_token.get_user(request)
    return request._cached_user

def get_token(request):
    if not hasattr(request, '_cached_token'):
        request._cached_token = auth_token.get_token(request)
    return request._cached_token


class TokenAuthenticationMiddlewares(object):
    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = SimpleLazyObject(lambda: get_token(request))
        request.user = SimpleLazyObject(lambda: get_user(request))

    def process_response(self, request, response):
        """
        Set cookie with token key if user is authenticated
        """
        # Save the session data and refresh the client cookie.
        # Skip session save for 500 responses, refs #3881.
        if response.status_code != 500 and hasattr(request, 'token') and request.token.is_active:
            if not request.token.expiration:
                max_age = config.AUTH_COOKIE_AGE
                expires_time = time.time() + max_age
                expires = cookie_date(expires_time)
            else:
                max_age = None
                expires = None

            request.token.save()
            response.set_cookie(config.AUTH_COOKIE_NAME, request.token.key, max_age=max_age, expires=expires)
        return response
