from django.core.urlresolvers import resolve
from django.contrib.auth.middleware import AuthenticationMiddleware as DjangoAuthenticationMiddleware
from django.contrib.auth import get_user


class RequestKwargsMiddleware(object):
    def process_request(self, request):
        request.kwargs = resolve(request.path).kwargs


'''class AuthenticationMiddleware(DjangoAuthenticationMiddleware):

    def process_request(self, request):
        assert hasattr(request, 'session'), "The Django authentication middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."

        request.user = SimpleLazyObject(lambda: get_user(request))'''
