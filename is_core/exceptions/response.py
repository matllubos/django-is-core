import mimeparse

from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.utils.encoding import force_text

from piston.converter import get_converter_from_request, get_supported_mime_types


def responseexception_factory(request, response_code, title, message, response_class=HttpResponse):
    rest_mime_types = list(get_supported_mime_types())
    ui_mime_types = ['text/html', 'application/xhtml+xml']

    best_match = mimeparse.best_match(rest_mime_types + ui_mime_types, request.META.get('HTTP_ACCEPT', 'text/html'))
    resp_message = message

    if best_match in ui_mime_types:
        if isinstance(resp_message, (list, tuple)):
            resp_message = ', '.join(resp_message)

        context = {'response_code': response_code, 'title': title, 'message': resp_message}
        content = render_to_string(('%s.html' % response_code, 'error.html'),
                                   context, context_instance=RequestContext(request))
        ct = None
    else:
        if resp_message:
            if isinstance(resp_message, (list, tuple)):
                resp_message = [force_text(val) for val in resp_message]
            else:
                resp_message = force_text(resp_message)
        else:
            resp_message = force_text(title)

        converter, ct = get_converter_from_request(request)
        content = converter().encode(request, {'message': resp_message}, None, message, ())
    return response_class(content, status=response_code, content_type=ct)
