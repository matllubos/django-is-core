from __future__ import unicode_literals

from django.core.urlresolvers import resolve
from django.contrib.auth.middleware import AuthenticationMiddleware as DjangoAuthenticationMiddleware
from django.contrib.auth import get_user
from django.http.response import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ValidationError
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_text

from is_core.exceptions import HttpRedirectException, HttpUnauthorizedException, HttpForbiddenException


class RequestKwargsMiddleware(object):

    def process_request(self, request):
        request.kwargs = resolve(request.path).kwargs


class HttpExceptionsMiddleware(object):

    # TODO: serialize exceptions according to Accept
    def process_exception(self, request, exception):
        if isinstance(exception, HttpRedirectException):
            return HttpResponseRedirect(exception.url)
        if isinstance(exception, ValidationError):
            return render_to_response('422.html', {'description': ', '.join(exception.messages)},
                                      context_instance=RequestContext(request))
        if isinstance(exception, HttpUnauthorizedException):
            return HttpResponse(status=401)
        if isinstance(exception, HttpForbiddenException):
            return HttpResponse(status=403)
