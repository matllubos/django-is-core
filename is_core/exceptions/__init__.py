from django.utils.translation import ugettext_lazy as _
from django.http.response import HttpResponseRedirect

from .response import responseexception_factory


class ResponseException(Exception):

    def __init__(self, message=None):
        self.message = message

    def get_response(self, request):
        return responseexception_factory(request, self.status_code, self.title, self.message)


class HttpRedirectException(ResponseException):

    def __init__(self, url):
        self.url = url

    def get_response(self, request):
        return HttpResponseRedirect(self.url)


class HttpUnauthorizedException(ResponseException):

    title = _('Unauthorized')
    status_code = 401


class HttpForbiddenException(ResponseException):

    title = _('Forbidden')
    status_code = 403

