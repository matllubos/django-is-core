from django.conf import settings
from django.http.response import Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.encoding import force_text

from pyston.conf import settings as pyston_settings
from pyston.forms import rest_modelform_factory
from pyston.exception import (RESTException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException, DataInvalidException, UnauthorizedException)
from pyston.resource import BaseResource, BaseModelResource, DefaultRESTModelResource
from pyston.response import RESTErrorResponse, RESTErrorsResponse
from pyston.utils import rfs

from chamber.shortcuts import get_object_or_none
from chamber.utils import transaction

from is_core.auth.permissions import (
    PermissionsSet, IsAuthenticated, CoreReadAllowed, CoreUpdateAllowed, CoreDeleteAllowed, CoreCreateAllowed,
    AllowAny
)
from is_core.config import settings
from is_core.exceptions.response import (HTTPBadRequestResponseException, HTTPUnsupportedMediaTypeResponseException,
                                         HTTPMethodNotAllowedResponseException, HTTPDuplicateResponseException,
                                         HTTPForbiddenResponseException)
from is_core.forms.models import smartmodelform_factory
from is_core.patterns import RESTPattern, patterns
from is_core.utils.compatibility import NoReverseMatch


class RESTPermissionsMixin:

    permission = IsAuthenticated()
    csrf_exempt = False

    def has_get_permission(self, **kwargs):
        return (
            self.permission.has_permission('get', self.request, self, obj=kwargs.get('obj')) and
            super().has_get_permission(**kwargs)
        )

    def has_post_permission(self, **kwargs):
        return (
            self.permission.has_permission('post', self.request, self, obj=kwargs.get('obj')) and
            super().has_post_permission(**kwargs)
        )

    def has_put_permission(self, **kwargs):
        return (
            self.permission.has_permission('put', self.request, self, obj=kwargs.get('obj')) and
            super().has_put_permission(**kwargs)
        )

    def has_patch_permission(self, **kwargs):
        return (
            self.permission.has_permission('patch', self.request, self, obj=kwargs.get('obj')) and
            super().has_patch_permission(**kwargs)
        )

    def has_delete_permission(self, **kwargs):
        return (
            self.permission.has_permission('delete', self.request, self, obj=kwargs.get('obj')) and
            super().has_delete_permission(**kwargs)
        )

    def has_options_permission(self, **kwargs):
        return (
            self._is_cors_options_request() or (
                self.permission.has_permission('options', self.request, self, obj=kwargs.get('obj')) and
                super().has_options_permission(**kwargs)
            )
        )

    def has_head_permission(self, **kwargs):
        return (
            self.permission.has_permission('head', self.request, self, obj=kwargs.get('obj')) and
            super().has_head_permission(**kwargs)
        )

    def _check_permission(self, name, *args, **kwargs):
        try:
            super()._check_permission(name, *args, **kwargs)
        except NotAllowedException:
            if not hasattr(self.request, 'user') or not self.request.user or not self.request.user.is_authenticated:
                raise UnauthorizedException
            else:
                raise


class RESTObjectPermissionsMixin(RESTPermissionsMixin):

    can_create_obj = True
    can_read_obj = True
    can_update_obj = True
    can_delete_obj = True

    def has_create_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('create_obj', self.request, self, obj=kwargs.get('obj')) and
            super().has_create_obj_permission(obj=obj, **kwargs)
        )

    def has_read_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('read_obj', self.request, self, obj=kwargs.get('obj')) and
            super().has_read_obj_permission(obj=obj, **kwargs)
        )

    def has_update_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('update_obj', self.request, self, obj=kwargs.get('obj')) and
            super().has_update_obj_permission(obj=obj, **kwargs)
        )

    def has_delete_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('delete_obj', self.request, self, obj=kwargs.get('obj')) and
            super().has_delete_obj_permission(obj=obj, **kwargs)
        )


class RESTResourceMixin:

    register = False
    abstract = True

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'core'):
            self.core.init_rest_request(request)
        return super(RESTResourceMixin, self).dispatch(request, *args, **kwargs)

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    def _get_error_response(self, exception):
        """
        Trasform pyston exceptions to Is-core exceptions and raise it
        """
        response_exceptions = {
            MimerDataException: HTTPBadRequestResponseException,
            NotAllowedException: HTTPForbiddenResponseException,
            UnsupportedMediaTypeException: HTTPUnsupportedMediaTypeResponseException,
            Http404: Http404,
            ResourceNotFoundException: Http404,
            NotAllowedMethodException: HTTPMethodNotAllowedResponseException,
            DuplicateEntryException: HTTPDuplicateResponseException,
            ConflictException: HTTPDuplicateResponseException,
        }
        response_exception = response_exceptions.get(type(exception))
        if response_exception:
            raise response_exception
        return super(RESTResourceMixin, self)._get_error_response(exception)


class RESTModelCoreResourcePermissionsMixin(RESTObjectPermissionsMixin):

    pk_name = 'pk'

    permission = PermissionsSet(
        # HTTP permissions
        head=CoreReadAllowed(),
        options=CoreReadAllowed(),
        post=CoreCreateAllowed(),
        get=CoreReadAllowed(),
        put=CoreUpdateAllowed(),
        patch=CoreUpdateAllowed(),
        delete=CoreDeleteAllowed(),

        # Serializer permissions
        create_obj=CoreCreateAllowed(),
        read_obj=CoreReadAllowed(),
        update_obj=CoreUpdateAllowed(),
        delete_obj=CoreDeleteAllowed()
    )

    def _get_perm_obj_or_none(self, pk=None):
        pk = pk or self.kwargs.get(self.pk_name)
        if pk:
            return get_object_or_none(self.core.model, pk=pk)
        else:
            return None


class RESTModelCoreMixin(RESTModelCoreResourcePermissionsMixin):

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_pk(self):
        return self.kwargs.get(self.pk_name)

    def _get_obj_or_none(self, pk=None):
        if pk or self._get_pk():
            return get_object_or_none(self._get_queryset(), pk=(pk or self._get_pk()))
        else:
            return None

    def _get_obj_or_404(self, pk=None):
         obj = self._get_obj_or_none(pk)
         if not obj:
             raise Http404
         return obj


class RESTResource(RESTPermissionsMixin, RESTResourceMixin, BaseResource):
    pass


class EntryPointResource(RESTResource):

    allowed_methods = ('get', 'head', 'options')
    permission = AllowAny()

    def get(self):
        out = {}
        for pattern_name, pattern in patterns.items():
            if isinstance(pattern, RESTPattern):
                try:
                    url = pattern.get_url_string(self.request)
                    allowed_methods = pattern.get_allowed_methods(self.request, None)
                    if allowed_methods:
                        out[pattern_name] = {'url': url, 'methods': allowed_methods}
                except NoReverseMatch:
                    pass

        return out


class RESTModelResource(RESTModelCoreMixin, RESTResourceMixin, BaseModelResource):

    form_class = None
    field_labels = None
    abstract = True
    filters = {}
    default_fields_extension = None

    def _get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None else self.core.get_rest_form_field_labels(self.request)
        )

    def get_fields(self, obj=None):
        fields = super(DefaultRESTModelResource, self).get_fields(obj=obj)
        return self.core.get_rest_fields(self.request, obj=None) if fields is None else fields

    def get_detailed_fields(self, obj=None):
        detailed_fields = super(DefaultRESTModelResource, self).get_detailed_fields(obj=obj)
        return self.core.get_rest_detailed_fields(self.request, obj=obj) if detailed_fields is None else detailed_fields

    def get_general_fields(self, obj=None):
        general_fields = super(DefaultRESTModelResource, self).get_general_fields(obj=obj)
        return self.core.get_rest_general_fields(self.request, obj=obj) if general_fields is None else general_fields

    def get_guest_fields(self, obj=None):
        guest_fields = super(DefaultRESTModelResource, self).get_guest_fields(obj=obj)
        return self.core.get_rest_guest_fields(self.request, obj=obj) if guest_fields is None else guest_fields

    def get_extra_fields(self, obj=None):
        extra_fields = super(DefaultRESTModelResource, self).get_extra_fields(obj=obj)
        return self.core.get_rest_extra_fields(self.request) if extra_fields is None else extra_fields

    def get_default_fields(self, obj=None):
        default_fields = super(DefaultRESTModelResource, self).get_default_fields(obj=obj)
        return self.core.get_rest_default_fields(self.request, obj=None) if default_fields is None else default_fields

    def get_extra_filter_fields(self):
        extra_filter_fields = super(DefaultRESTModelResource, self).get_extra_filter_fields()
        return self.core.get_rest_extra_filter_fields(self.request) if extra_filter_fields is None else extra_filter_fields

    def get_filter_fields(self):
        filter_fields = super(DefaultRESTModelResource, self).get_filter_fields()
        return self.core.get_rest_filter_fields(self.request) if filter_fields is None else filter_fields

    def get_extra_order_fields(self):
        extra_order_fields = super(DefaultRESTModelResource, self).get_extra_order_fields()
        return self.core.get_rest_extra_order_fields(self.request) if extra_order_fields is None else extra_order_fields

    def get_order_fields(self):
        order_fields = super(DefaultRESTModelResource, self).get_order_fields()
        return self.core.get_rest_order_fields(self.request) if order_fields is None else order_fields

    def get_default_fields_rfs(self, obj=None):
        return super(RESTModelResource, self).get_default_fields_rfs(obj=obj).join(
            rfs(self.get_default_fields_extension(obj))
        )

    def get_default_fields_extension(self, obj=None):
        return (
            self.core.get_rest_default_fields_extension(self.request, obj=None)
            if self.default_fields_extension is None else self.default_fields_extension
        )

    def _rest_links(self, obj):
        rest_links = {}
        for pattern in self.core.rest_patterns.values():
            if pattern.send_in_rest:
                url = pattern.get_url_string(self.request, obj=obj)
                if url:
                    allowed_methods = pattern.get_allowed_methods(self.request, obj)
                    if allowed_methods:
                        rest_links[pattern.name] = {
                            'url': url,
                            'methods': [method.upper() for method in allowed_methods]
                        }
        return rest_links

    def _default_action(self, obj):
        return self.core.get_default_action(self.request, obj=obj)

    def _actions(self, obj):
        return self.core.get_list_actions(self.request, obj)

    def _class_names(self, obj):
        return self.core.get_rest_obj_class_names(self.request, obj)

    def get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_headers_queryset_context_mapping(self):
        mapping = super(RESTModelResource, self)._get_headers_queryset_context_mapping()
        mapping.update({
            'direction': ('HTTP_X_DIRECTION', '_direction'),
            'order': ('HTTP_X_ORDER', '_order')
        })
        return mapping

    def _preload_queryset(self, qs):
        return self.core.preload_queryset(self.request, qs)

    def _get_exclude(self, obj=None):
        return self.core.get_rest_form_exclude(self.request, obj)

    def _get_form_fields(self, obj=None):
        return self.core.get_rest_form_fields(self.request, obj)

    def _get_form_class(self, obj=None):
        return (
            self.form_class or
            (
                self.core.get_rest_form_edit_class(self.request, obj)
                if obj
                else self.core.get_rest_form_add_class(self.request, obj)
            )
        )

    def _get_form_initial(self, obj):
        return {'_request': self.request, '_user': self.request.user}

    def _pre_save_obj(self, obj, form, change):
        self.core.pre_save_model(self.request, obj, form, change)

    def _save_obj(self, obj, form, change):
        self.core.save_model(self.request, obj, form, change)

    def _post_save_obj(self, obj, form, change):
        self.core.post_save_model(self.request, obj, form, change)

    def _pre_delete_obj(self, obj):
        self.core.pre_delete_model(self.request, obj)

    def _delete_obj(self, obj):
        self.core.delete_model(self.request, obj)

    def _post_delete_obj(self, obj):
        self.core.post_delete_model(self.request, obj)

    def _generate_form_class(self, inst, exclude=[]):
        form_class = self._get_form_class(inst)
        exclude = list(self._get_exclude(inst)) + exclude
        fields = self._get_form_fields(inst)
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return rest_modelform_factory(self.model, form=form_class, form_factory=smartmodelform_factory,
                                      auto_related_direct_fields=pyston_settings.AUTO_RELATED_DIRECT_FIELDS,
                                      auto_related_reverse_fields=pyston_settings.AUTO_RELATED_REVERSE_FIELDS,
                                      request=self.request, exclude=exclude, fields=fields,
                                      labels=self._get_field_labels())

    def put(self):
        # TODO: backward compatibility for bulk update should be used only patch
        return super(RESTModelResource, self).put() if self.kwargs.get(self.pk_name) else self.update_bulk()

    def patch(self):
        return super(RESTModelResource, self).patch() if self.kwargs.get(self.pk_name) else self.update_bulk()

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    @transaction.atomic
    def update_bulk(self):
        qs = self._filter_queryset(self._get_queryset())
        BULK_CHANGE_LIMIT = getattr(settings, 'BULK_CHANGE_LIMIT', 200)
        if qs.count() > BULK_CHANGE_LIMIT:
            return RESTErrorResponse(
                msg=ugettext('Only %s objects can be changed by one request').format(BULK_CHANGE_LIMIT),
                code=413)

        data = self.get_dict_data()
        objects, errors = zip(*(self._update_obj(obj, data) for obj in qs))
        compact_errors = tuple(err for err in errors if err)
        return RESTErrorsResponse(compact_errors) if len(compact_errors) > 0 else objects

    def _update_obj(self, obj, data):
        try:
            return (
                self._create_or_update({
                    self.pk_field_name: obj.pk,
                    **data,
                }, partial_update=True),
                None
            )
        except DataInvalidException as ex:
            return (None, self._format_message(obj, ex))
        except (ConflictException, NotAllowedException):
            raise
        except RESTException as ex:
            return (None, self._format_message(obj, ex))

    def _extract_message(self, ex):
        return '\n'.join([force_text(v) for v in ex.errors.values()]) if hasattr(ex, 'errors') else ex.message

    def _format_message(self, obj, ex):
        return {
            'id': obj.pk,
            'errors': {k: mark_safe(force_text(v)) for k, v in ex.errors.items()} if hasattr(ex, 'errors') else {},
            '_obj_name': force_text(obj),
        }


class UIRESTModelResource(RESTModelResource):

    def _web_links(self, obj):
        web_links = {}
        for pattern in self.core.web_link_patterns(self.request):
            if pattern.send_in_rest:
                url = pattern.get_url_string(self.request, obj=obj)
                if url and pattern.has_permission('get', self.request, obj=obj):
                    web_links[pattern.name] = url
        return web_links

    def _class_names(self, obj):
        return self.core.get_rest_obj_class_names(self.request, obj)
