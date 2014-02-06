from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from django.http.response import HttpResponseNotAllowed, Http404
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet

from piston.utils import HttpStatusCode, rc
from piston.resource import Resource, CHALLENGE
from piston.handler import typemapper
from piston.utils import MimerDataException, translate_mime, UnsupportedMediaTypeException, coerce_put_post

from emitters import Emitter
from handler import HeadersResult


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

        try:
            emitter, ct = Emitter.get(em_format)
            fields = handler.fields

            # Lubos: I turned list_fields for obj_fields, because when emmiter serialize foreign key objects it should
            # use list_fields. But standard django piston use fields
            if hasattr(handler, 'obj_fields') and not isinstance(result, (list, tuple, QuerySet)):
                fields = handler.obj_fields
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
        srl = emitter(result, typemapper, handler, request, fields, anonymous, fun_kwargs=fun_kwargs)

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
                for header, value in http_headers.items():
                    resp[header] = value
            else:
                resp = stream

            resp.streaming = self.stream

            return resp
        except HttpStatusCode, e:
            return e.response

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
        super(DynamicRestHandlerResource, self).__init__(handler, authentication=authentication)


class RestModelResource(DynamicRestHandlerResource):

    def __init__(self, name, core, model=None, form_class=None, list_fields=None, obj_fields=None, site_name=None,
                 menu_group=None, menu_subgroup=None, allowed_methods=None, exclude=None, handler_class=None):
        model = model or core.model
        form_class = form_class or core.form_class
        list_fields = list_fields or core.get_rest_list_fields()
        obj_fields = obj_fields or core.get_rest_obj_fields()
        site_name = site_name or core.site_name
        menu_group = menu_group or core.menu_group
        menu_subgroup = menu_subgroup or core.menu_subgroup
        allowed_methods = allowed_methods or core.rest_allowed_methods
        exclude = exclude or core.exclude
        handler_class = handler_class or core.rest_handler


        list_fields, obj_fields = self.get_fields(obj_fields, list_fields, model, core)
        kwargs = {
                  'model': model, 'fields': list_fields, 'obj_fields': obj_fields, 'form_class': form_class,
                  'site_name': site_name, 'menu_group': menu_group, 'menu_subgroup': menu_subgroup,
                  'core': core, 'allowed_methods': allowed_methods, 'exclude': exclude
                  }
        super(RestModelResource, self).__init__(handler_class, name, **kwargs)

    def get_fields(self, obj_fields, list_fields, model, core):
        from is_core.main import UIRestModelISCore

        obj_fields = list(obj_fields)
        if not obj_fields:
            for field in model._meta.fields:
                if isinstance(field, ForeignKey):
                    obj_fields.append((field.name, ()))
                else:
                    obj_fields.append(field.name)
            obj_fields += list_fields
        fields = list(list_fields)
        for default_field in ['id', '_rest_links', '_obj_name']:
            fields.append(default_field)
            obj_fields.append(default_field)

        if isinstance(core, UIRestModelISCore):
            fields.append('_web_links')
            obj_fields.append('_web_links')
        return fields, obj_fields
