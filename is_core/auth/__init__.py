from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.utils.functional import SimpleLazyObject

from is_core.utils.models import get_object_or_none


def get_obj(Model, pk):
    return get_object_or_none(Model, pk=pk)


class Auth(object):

    def __init__(self, permissions_validators, **kwargs):
        self.permissions_validators = permissions_validators
        self.kwargs = kwargs

    def is_authenticated(self, request):
        rm = request.method.upper()

        if not request.user or not request.user.is_active:
            return False

        if not self.permissions_validators.has_key(rm):
            return False

        validators = self.permissions_validators.get(rm)

        if not isinstance(validators, (list, tuple)):
            validators = [validators]

        for validator in validators:
            if validator(request, **self.validator_kwargs(request, validator)):
                return True
        return False

    def validator_kwargs(self, request, validator):
        if request.kwargs.has_key('pk'):
            if hasattr(validator.im_self, 'model'):
                return {'obj': SimpleLazyObject(lambda: get_obj(validator.im_self.model, request.kwargs['pk']))}
        return {}


class AuthWrapper(Auth):

    def wrap(self, func):

        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated() and not self.is_authenticated(request):
                return HttpResponseForbidden(render_to_string('403.html', context_instance=RequestContext(request)))

            return login_required(func)(request, *args, **kwargs)

        return wrapper


class RestAuthWrapper(Auth):

    def wrap(self, func):

        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated() or not self.is_authenticated(request):
                return HttpResponseForbidden()

            return func(request, *args, **kwargs)

        return wrapper