from __future__ import unicode_literals

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.utils.functional import SimpleLazyObject
from django.utils.decorators import available_attrs
from django.conf import settings

from chamber.shortcuts import get_object_or_none

from is_core.exceptions import HttpUnauthorizedResponseException


def rest_login_required(rest_func):

    @wraps(rest_func, assigned=available_attrs(rest_func))
    def _rest_login_requiered(request, *args, **kwargs):
        if (not hasattr(request, 'user') or not request.user or not request.user.is_authenticated() and
                (request.method.lower() != 'options' or not getattr(settings, 'PISTON_CORS', False))):
            raise HttpUnauthorizedResponseException
        return rest_func(request, *args, **kwargs)

    return _rest_login_requiered
