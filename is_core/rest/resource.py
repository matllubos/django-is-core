'''from __future__ import unicode_literals

from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from django.http.response import HttpResponseNotAllowed, Http404
from django.db.models.query import QuerySet

from piston.utils import HttpStatusCode, rc
from piston.resource import Resource, CHALLENGE
from piston.handler import typemapper
from piston.utils import MimerDataException, translate_mime, UnsupportedMediaTypeException, coerce_put_post, \
                         list_to_dict, dict_to_list, flat_list
from piston.emitters import Emitter

from handler import HeadersResult

from is_core import *
from is_core.rest.auth import RestAuthentication
from is_core.auth_token.wrappers import RestTokenAuthentication


class RestResource(Resource):

    def __init__(self, handler, authentication=None, **kwargs):
        super(RestResource, self).__init__(handler, authentication=authentication)
        for attr_key, attr_val in kwargs.items():
            setattr(self.handler, attr_key, attr_val)

    # This is nessesary beacouse django piston not support http headers inside response
    # I am very lazy to refactor it, because piston developer was terrible pig
    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        return self.handler.call(request, *args, **kwargs)


class DynamicRestHandlerResource(RestResource):

    def __init__(self, handler_class, name=None, authentication=None, **kwargs):
        if name == None:
            name = handler_class.__name__
        handler = type(str(name), (handler_class,), kwargs)
        if handler.login_required:
            if config.AUTH_USE_TOKENS:
                authentication = authentication or RestTokenAuthentication(handler.get_permission_validators())
            else:
                authentication = authentication or RestAuthentication(handler.get_permission_validators())
        super(DynamicRestHandlerResource, self).__init__(handler, authentication=authentication)


class RestModelResource(DynamicRestHandlerResource):

    def __init__(self, name, core, model=None, form_class=None, fields=None, default_list_fields=None,
                 default_obj_fields=None, site_name=None, menu_group=None, allowed_methods=None,
                 form_exclude=None, handler_class=None):
        model = model or core.model

        fields = fields or core.get_rest_fields()
        default_list_fields = default_list_fields or core.get_rest_default_list_fields()
        default_obj_fields = default_obj_fields or core.get_rest_default_obj_fields()

        site_name = site_name or core.site_name
        menu_group = menu_group or core.menu_group
        allowed_methods = allowed_methods or core.rest_allowed_methods
        handler_class = handler_class or core.rest_handler

        fields = self.get_handler_fields(fields, model, core)
        kwargs = {
                  'model': model, 'fields': fields, 'default_list_fields': default_list_fields,
                  'default_obj_fields': default_obj_fields, 'form_class': form_class,
                  'site_name': site_name, 'menu_group': menu_group, 'core': core,
                  'allowed_methods': allowed_methods
                  }
        self.core = core
        super(RestModelResource, self).__init__(handler_class, name, **kwargs)

    def __call__(self, request, *args, **kwargs):
        self.core.init_request(request)
        return super(RestModelResource, self).__call__(request, *args, **kwargs)

    def get_handler_fields(self, fields, model, core):
        from is_core.main import UIRestModelISCore

        extra_fields = ('id', '_obj_name', '_rest_links', '_actions', '_class_names')
        if isinstance(core, UIRestModelISCore):
            extra_fields += ('_web_links',)

        return fields + extra_fields'''
