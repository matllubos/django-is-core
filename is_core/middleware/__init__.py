from __future__ import unicode_literals

from django.core.urlresolvers import resolve
from django.contrib.auth.middleware import AuthenticationMiddleware as DjangoAuthenticationMiddleware
from django.contrib.auth import get_user
from django.http.response import HttpResponseRedirect

from is_core.exceptions import HttpRedirectException


class RequestKwargsMiddleware(object):

    def process_request(self, request):
        request.kwargs = resolve(request.path).kwargs


class HttpExceptionsMiddleware(object):

    def process_exception(self, request, exception):
        if isinstance(exception, HttpRedirectException):
            return HttpResponseRedirect(exception.url)
