import mimeparse

from django.conf import settings
from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from pyston.utils import set_rest_context_to_request
from pyston.utils.helpers import str_to_class
from pyston.converters import get_converter, get_supported_mime_types, get_converter_name_from_request
from pyston.resource import BaseResource
from pyston.conf import settings as pyston_settings


def response_exception_factory(request, response_code, title, message, response_class=HttpResponse):
    rest_mime_types = list(get_supported_mime_types())
    ui_mime_types = ['text/html', 'application/xhtml+xml']

    best_match = mimeparse.best_match(rest_mime_types + ui_mime_types, request.META.get('HTTP_ACCEPT', 'text/html'))
    resp_message = message

    if best_match in ui_mime_types:
        if isinstance(resp_message, (list, tuple)):
            resp_message = ', '.join(resp_message)

        return response_class(
            render_to_string(
                ('{}.html'.format(response_code), 'error.html'),
                {'response_code': response_code, 'title': title, 'message': resp_message},
                request=request
            ),
            status=response_code
        )
    else:
        resp_message = (
            ', '.join([force_text(val) for val in resp_message])
            if isinstance(resp_message, (list, tuple))
            else force_text(resp_message)
        ) if resp_message else force_text(title)
        set_rest_context_to_request(request, BaseResource.DEFAULT_REST_CONTEXT_MAPPING)
        converter_name = get_converter_name_from_request(request)
        converter = get_converter(converter_name)
        response = response_class(status=response_code, content_type=converter.content_type)

        rest_error_response = str_to_class(pyston_settings.ERROR_RESPONSE_CLASS)

        converter.encode_to_stream(response, rest_error_response(msg=resp_message, code=response_code).result)
        return response


class ResponseException(Exception):

    def __init__(self, message=None):
        self.message = message

    def get_response(self, request):
        return response_exception_factory(request, self.status_code, self.title, self.message)


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
