from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.utils.functional import SimpleLazyObject

from is_core.utils.models import get_object_or_none
from is_core import config


def get_obj(Model, pk):
    try:
        return get_object_or_none(Model, pk=pk)
    except ValueError:
        return None


class Auth(object):

    def __init__(self, permissions_validators, **kwargs):
        self.permissions_validators = permissions_validators
        self.kwargs = kwargs

    def is_authenticated(self, request):
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated():
            return False

        return self.has_permissions(request)

    def has_permissions(self, request):
        rm = request.method.upper()

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


class PermWrapper(Auth):

    def _check_permissions(self, request):
        raise NotImplemented()

    def _forbidden(self, request):
        return HttpResponseForbidden()

    def _wrap(self, func, request, *args, **kwargs):
        return func(request, *args, **kwargs)

    def wrap(self, func):

        def wrapper(request, *args, **kwargs):
            if not self._check_permissions(request):
                return self._forbidden(request)

            return self._wrap(func, request, *args, **kwargs)

        return wrapper


class UIPermWrapper(PermWrapper):

    def _check_permissions(self, request):
        return self.has_permissions(request)

    def _forbidden(self, request):
        return HttpResponseForbidden(render_to_string('403.html', context_instance=RequestContext(request)))


class UIAuthPermWrapper(UIPermWrapper):

    def _check_permissions(self, request):
        return not request.user.is_authenticated() or self.is_authenticated(request)

    def _wrap(self, func, request, *args, **kwargs):
        return login_required(func)(request, *args, **kwargs)


class RestPermWrapper(PermWrapper):

    def _check_permissions(self, request):
        return self.has_permissions(request)


class RestAuthPermWrapper(RestPermWrapper):

    def _check_permissions(self, request):
        return self.is_authenticated(request)
