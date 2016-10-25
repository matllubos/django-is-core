import mimeparse

import django

from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from pyston.utils import set_rest_context_to_request
from pyston.converter import get_converter_from_request, get_supported_mime_types
from pyston.resource import BaseResource


def responseexception_factory(request, response_code, title, message, response_class=HttpResponse):
    rest_mime_types = list(get_supported_mime_types())
    ui_mime_types = ['text/html', 'application/xhtml+xml']

    best_match = mimeparse.best_match(rest_mime_types + ui_mime_types, request.META.get('HTTP_ACCEPT', 'text/html'))
    resp_message = message

    if best_match in ui_mime_types:
        if isinstance(resp_message, (list, tuple)):
            resp_message = ', '.join(resp_message)

        context = {'response_code': response_code, 'title': title, 'message': resp_message}
        content = render_to_string(('{}.html'.format(response_code), 'error.html'), context, request=request)
        ct = None
    else:
        if resp_message:
            if isinstance(resp_message, (list, tuple)):
                resp_message = [force_text(val) for val in resp_message]
            else:
                resp_message = force_text(resp_message)
        else:
            resp_message = force_text(title)
        set_rest_context_to_request(request, BaseResource.DEFAULT_REST_CONTEXT_MAPPING)
        converter, ct = get_converter_from_request(request)
        content = converter().encode({'message': {'error': resp_message}})
    return response_class(content, status=response_code, content_type=ct)


class ResponseException(Exception):

    def __init__(self, message=None):
        self.message = message

    def get_response(self, request):
        return responseexception_factory(request, self.status_code, self.title, self.message)


class HTTPRedirectResponseException(ResponseException):

    def __init__(self, url):
        self.url = url

    def get_response(self, request):
        return HttpResponseRedirect(self.url)


class HTTPBadRequestResponseException(ResponseException):

    title = _('Bad Request')
    status_code = 400


class HTTPUnauthorizedResponseException(ResponseException):

    title = _('Unauthorized')
    status_code = 401


class HTTPForbiddenResponseException(ResponseException):

    title = _('Forbidden')
    status_code = 403


class HTTPUnsupportedMediaTypeResponseException(ResponseException):

    title = _('Unsupported Media Type')
    status_code = 415


class HTTPMethodNotAllowedResponseException(ResponseException):

    title = _('Method Not Allowed')
    status_code = 405


class HTTPDuplicateResponseException(ResponseException):

    title = _('Conflict/Duplicate')
    status_code = 409


class HTTPServiceUnavailableException(ResponseException):

    title = _('Temporarily unavailable')
    status_code = 503
