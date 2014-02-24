from django.core.urlresolvers import resolve
from django.contrib.auth.middleware import AuthenticationMiddleware as DjangoAuthenticationMiddleware
from django.contrib.auth import get_user


class RequestKwargsMiddleware(object):
    def process_request(self, request):
        request.kwargs = resolve(request.path).kwargs

