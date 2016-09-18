from __future__ import unicode_literals

import time

from django.utils.functional import SimpleLazyObject
from django.utils.http import cookie_date
from django.utils.encoding import force_text

from is_core import config
from is_core.auth_token import utils


def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = utils.get_user(request)
    return request._cached_user


class TokenAuthenticationMiddlewares(object):

    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = utils.get_token(request)
        request.user = SimpleLazyObject(lambda: get_user(request))
        request._dont_enforce_csrf_checks = utils.dont_enforce_csrf_checks(request)

    def process_response(self, request, response):
        """
        Set cookie with token key if user is authenticated
        """
        # Save the session data and refresh the client cookie.
        # Skip session save for 500 responses, refs #3881.
        if response.status_code != 500 and hasattr(request, 'token') and request.token.is_active:
            if not request.token.expiration:
                max_age = config.IS_CORE_AUTH_COOKIE_AGE
                expires_time = time.time() + max_age
                expires = cookie_date(expires_time)
            else:
                max_age = None
                expires = None

            request.token.save()
            response.set_cookie(config.IS_CORE_AUTH_COOKIE_NAME, force_text(request.token.key), max_age=max_age,
                                expires=expires, httponly=config.IS_CORE_AUTH_COOKIE_HTTPONLY,
                                secure=config.IS_CORE_AUTH_COOKIE_SECURE, domain=config.IS_CORE_AUTH_COOKIE_DOMAIN)
        return response
