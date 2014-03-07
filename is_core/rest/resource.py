from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from django.http.response import HttpResponseNotAllowed, Http404
from django.db.models.query import QuerySet

from piston.utils import HttpStatusCode, rc
from piston.resource import Resource, CHALLENGE
from piston.handler import typemapper
from piston.utils import MimerDataException, translate_mime, UnsupportedMediaTypeException, coerce_put_post

from emitters import Emitter

from handler import HeadersResult

from is_core.rest.auth import RestAuthentication
from is_core.rest.utils import list_to_dict, dict_to_list, flat_list
from is_core import config
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
        rm = request.method.upper()

        # Django's internal mechanism doesn't pick up
        # PUT request, so we trick it a little here.
        if rm == "PUT":
            coerce_put_post(request)

        actor, anonymous = self.authenticate(request, rm)

        if anonymous is CHALLENGE:
            return actor()
        else:
            handler = actor

        result = self.get_result(request, handler, rm, *args, **kwargs)

        status_code = 200
        http_headers = {}

        if isinstance(result, HeadersResult):
            http_headers = result.http_headers
            status_code = result.status_code
            result = result.result

        # Support emitter through (?P<emitter_format>) and ?format=emitter
        # and lastly Accept: header processing
        em_format = self.determine_emitter(request, *args, **kwargs)
        if not em_format:
            request_has_accept = 'HTTP_ACCEPT' in request.META
            if request_has_accept and self.strict_accept:
                return rc.NOT_ACCEPTABLE
            em_format = self.default_emitter

        kwargs.pop('emitter_format', None)

        if isinstance(result, (list, tuple, QuerySet)):
            concrete_object = False
        else:
            concrete_object = True

        try:
            emitter, ct = Emitter.get(em_format)

            fields = self.get_fields(request, handler, concrete_object)
        except ValueError:
            result = rc.BAD_REQUEST
            result.content = "Invalid output format specified '%s'." % em_format
            return result

        # If we're looking at a response object which contains non-string
        # content, then assume we should use the emitter to format that
        # content
        if isinstance(result, HttpResponse) and not isinstance(result.content, str):
            status_code = result.status_code
            # Note: We can't use result.content here because that method attempts
            # to convert the content into a string which we don't want.
            # when _is_string is False _container is the raw data
            result = result._container

        fun_kwargs = {'request': request}

        srl = emitter(result, typemapper, handler, request, self.get_serialization_format(request), fields, anonymous,
                      fun_kwargs=fun_kwargs)

        try:
            """
            Decide whether or not we want a generator here,
            or we just want to buffer up the entire result
            before sending it to the client. Won't matter for
            smaller datasets, but larger will have an impact.
            """

            if self.stream: stream = srl.stream_render(request)
            else: stream = srl.render(request)

            if not isinstance(stream, HttpResponse):
                resp = HttpResponse(stream, content_type=ct, status=status_code)
            else:
                resp = stream

            for header, value in self.get_headers(request, handler, http_headers, concrete_object).items():
                resp[header] = value

            resp.streaming = self.stream

            return resp
        except HttpStatusCode, e:
            return e.response

    def get_headers(self, request, handler, http_headers, concrete_obj):
        http_headers['X-Serialization-Format-Options'] = ','.join(Emitter.SerializationTypes)
        return http_headers

    def get_serialization_format(self, request):
        serialization_format = request.META.get('HTTP_X_SERIALIZATION_FORMAT', Emitter.SerializationTypes.RAW)
        if serialization_format not in Emitter.SerializationTypes:
            return Emitter.SerializationTypes.RAW
        return serialization_format

    def get_fields(self, request, handler, concrete_obj):
        return handler.fields

    def get_result(self, request, handler, rm, *args, **kwargs):
        """
        NB: Sends a `Vary` header so we don't cache requests
        that are different (OAuth stuff in `Authorization` header.)
        """

        # Translate nested datastructs into `request.data` here.
        if rm in ('POST', 'PUT'):
            try:
                translate_mime(request)
            except MimerDataException:
                return rc.BAD_REQUEST
            except UnsupportedMediaTypeException:
                return rc.UNSUPPORTED_MEDIA_TYPE

            if not hasattr(request, 'data'):
                if rm == 'POST':
                    request.data = request.POST
                else:
                    request.data = request.PUT

        if not rm in handler.allowed_methods:
            return HttpResponseNotAllowed(handler.allowed_methods)

        meth = getattr(handler, self.callmap.get(rm, ''), None)
        if not meth:
            raise Http404

        # Support emitter through (?P<emitter_format>) and ?format=emitter
        # and lastly Accept: header processing
        em_format = self.determine_emitter(request, *args, **kwargs)
        if not em_format:
            request_has_accept = 'HTTP_ACCEPT' in request.META
            if request_has_accept and self.strict_accept:
                return rc.NOT_ACCEPTABLE
            em_format = self.default_emitter

        kwargs.pop('emitter_format', None)

        # Clean up the request object a bit, since we might
        # very well have `oauth_`-headers in there, and we
        # don't want to pass these along to the handler.
        request = self.cleanup_request(request)

        try:
            result = meth(request, *args, **kwargs)
        except Exception, e:
            result = self.error_handler(e, request, meth, em_format)

        return result


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
                 default_obj_fields=None, site_name=None, menu_group=None, menu_subgroup=None, allowed_methods=None,
                 exclude=None, handler_class=None):
        model = model or core.model
        form_class = form_class or core.form_class

        fields = fields or core.get_rest_fields()
        default_list_fields = default_list_fields or core.get_rest_default_list_fields()
        default_obj_fields = default_obj_fields or core.get_rest_default_obj_fields()

        site_name = site_name or core.site_name
        menu_group = menu_group or core.menu_group
        menu_subgroup = menu_subgroup or core.menu_subgroup
        allowed_methods = allowed_methods or core.rest_allowed_methods
        exclude = exclude or core.exclude
        handler_class = handler_class or core.rest_handler

        fields = self.get_handler_fields(fields, model, core)
        kwargs = {
                  'model': model, 'fields': fields, 'default_list_fields': default_list_fields,
                  'default_obj_fields': default_obj_fields, 'form_class': form_class,
                  'site_name': site_name, 'menu_group': menu_group, 'menu_subgroup': menu_subgroup,
                  'core': core, 'allowed_methods': allowed_methods, 'exclude': exclude
                  }
        super(RestModelResource, self).__init__(handler_class, name, **kwargs)

    # TODO: maybe cache dict fields
    def get_fields(self, request, handler, concrete_obj):
        allowed_fields = list_to_dict(handler.fields)

        fields = {}
        x_fields = request.META.get('HTTP_X_FIELDS', '')
        for field in x_fields.split(','):
            if field in allowed_fields:
                fields[field] = allowed_fields.get(field)

        if fields:
            return dict_to_list(fields)

        if concrete_obj:
            fields = handler.default_obj_fields
        else:
            fields = handler.default_list_fields
        fields = list_to_dict(fields)

        x_extra_fields = request.META.get('HTTP_X_EXTRA_FIELDS', '')
        for field in x_extra_fields.split(','):
            if field in allowed_fields:
                fields[field] = allowed_fields.get(field)

        return dict_to_list(fields)

    def get_headers(self, request, handler, default_http_headers, concrete_obj):
        headers = super(RestModelResource, self).get_headers(request, handler, default_http_headers, concrete_obj)
        headers['X-Fields-Options'] = ','.join(flat_list(handler.fields))
        return headers

    def get_handler_fields(self, fields, model, core):
        from is_core.main import UIRestModelISCore

        extra_fields = ('id', '_obj_name', '_rest_links', '_actions', '_class_names')
        if isinstance(core, UIRestModelISCore):
            extra_fields += ('_web_links',)

        return fields + extra_fields
