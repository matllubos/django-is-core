from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.core.urlresolvers import resolve
from django.http.response import HttpResponse
from django.utils.encoding import force_text

from piston.serializer import determine_emitter
from piston.emitters import Emitter
from piston.resource import typemapper

from is_core.patterns import reverse_pattern, RestPattern


def throttling_failure_view(request, exception):
    if isinstance(reverse_pattern(resolve(request.path).url_name), RestPattern):
        em_format = determine_emitter(request)
        emitter, _ = Emitter.get(em_format)
        srl = emitter({'messages': {'error': force_text(exception)}}, typemapper, None, request,
                      Emitter.SERIALIZATION_TYPES.RAW)
        return HttpResponse(content=srl.render(request), status=429)

    response = render_to_response('429.html', {'description': force_text(exception)},
                                  context_instance=RequestContext(request))
    response.status_code = 429
    return response
