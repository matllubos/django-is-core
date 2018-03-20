from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.utils.functional import SimpleLazyObject
from django.utils.decorators import available_attrs

from chamber.shortcuts import get_object_or_none

from is_core import config
from is_core.exceptions import HTTPUnauthorizedResponseException


def rest_login_required(rest_func):

    @wraps(rest_func, assigned=available_attrs(rest_func))
    def _rest_login_required(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            raise HTTPUnauthorizedResponseException
        return rest_func(request, *args, **kwargs)

    return _rest_login_required
