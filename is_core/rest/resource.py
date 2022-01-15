from functools import wraps

from django.conf import settings as django_settings
from django.http.response import Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.encoding import force_text
from django.urls import NoReverseMatch

from pyston.conf import settings as pyston_settings
from pyston.forms import rest_modelform_factory
from pyston.exception import (RestException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException, DataInvalidException, UnauthorizedException)
from pyston.resource import BaseResource, DjangoResource
from pyston.response import RestErrorResponse, RestErrorsResponse

from chamber.shortcuts import get_object_or_none
from chamber.utils import transaction

from is_core.auth.permissions import (
    PermissionsSet, IsAuthenticated, CoreAllowed, CoreReadAllowed, CoreUpdateAllowed, CoreDeleteAllowed,
    CoreCreateAllowed, AllowAny, DEFAULT_PERMISSION
)
from is_core.auth.views import FieldPermissionViewMixin
from is_core.exceptions.response import (HttpBadRequestResponseException, HttpUnsupportedMediaTypeResponseException,
                                         HttpMethodNotAllowedResponseException, HttpDuplicateResponseException,
                                         HttpForbiddenResponseException)
from is_core.forms.models import smartmodelform_factory
from is_core.patterns import RestPattern, patterns
from is_core.utils import get_field_label_from_path, METHOD_OBJ_STR_NAME, LOOKUP_SEP

from .filters import CoreDjangoFilterManager


class PermissionsResourceMixin:

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


class PermissionsModelResourceMixin(PermissionsResourceMixin):

    can_create_obj = True
    can_read_obj = True
    can_update_obj = True
    can_delete_obj = True

    def has_create_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('create_obj', self.request, self, obj=obj) and
            super().has_create_obj_permission(obj=obj, **kwargs)
        )

    def has_read_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('read_obj', self.request, self, obj=obj) and
            super().has_read_obj_permission(obj=obj, **kwargs)
        )

    def has_update_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('update_obj', self.request, self, obj=obj) and
            super().has_update_obj_permission(obj=obj, **kwargs)
        )

    def has_delete_obj_permission(self, obj=None, **kwargs):
        return (
            self.permission.has_permission('delete_obj', self.request, self, obj=obj) and
            super().has_delete_obj_permission(obj=obj, **kwargs)
        )


class CoreResourceMixin:

    register = False
    abstract = True

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'core'):
            self.core.init_rest_request(request)
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    def _get_error_response(self, exception):
        """
        Trasform pyston exceptions to Is-core exceptions and raise it
        """
        response_exceptions = {
            MimerDataException: HttpBadRequestResponseException,
            NotAllowedException: HttpForbiddenResponseException,
            UnsupportedMediaTypeException: HttpUnsupportedMediaTypeResponseException,
            Http404: Http404,
            ResourceNotFoundException: Http404,
            NotAllowedMethodException: HttpMethodNotAllowedResponseException,
            DuplicateEntryException: HttpDuplicateResponseException,
            ConflictException: HttpDuplicateResponseException,
        }
        response_exception = response_exceptions.get(type(exception))
        if response_exception:
            raise response_exception
        return super()._get_error_response(exception)

    @classmethod
    def get_method_returning_field_value(cls, field_name):
        """
        Field values can be obtained from resource or core.
        """
        method = super().get_method_returning_field_value(field_name)

        if method:
            return method

        core_method = cls.core.get_method_returning_field_value(field_name)
        if core_method:
            @wraps(core_method)
            def core_method_wrapper(self, **kwargs):
                return core_method(self.core, **kwargs)
            return core_method_wrapper

        return None


class PermissionsModelCoreResourceMixin(PermissionsModelResourceMixin):

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
        delete_obj=CoreDeleteAllowed(),

        # Other permissions
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    def _get_perm_obj_or_none(self, pk=None):
        pk = pk or self.kwargs.get(self.pk_name)
        if pk:
            return get_object_or_none(self.core.model, pk=pk)
        else:
            return None


class CoreResource(PermissionsResourceMixin, CoreResourceMixin, BaseResource):
    pass


class EntryPointResource(CoreResource):

    allowed_methods = ('get', 'head', 'options')
    permission = AllowAny()

    def get(self):
        out = {}
        for pattern_name, pattern in patterns.items():
            if isinstance(pattern, RestPattern):
                try:
                    url = pattern.get_url_string(self.request)
                    allowed_methods = pattern.get_allowed_methods(self.request, None)
                    if allowed_methods:
                        out[pattern_name] = {'url': url, 'methods': allowed_methods}
                except NoReverseMatch:
                    pass

        return out


class SmartFormDjangoResource(DjangoResource):

    def _generate_form_class(self, inst, exclude=None):
        exclude = [] if exclude is None else exclude
        exclude = list(self._get_exclude(inst)) + exclude
        form_class = self._get_form_class(inst)
        fields = self._get_form_fields(inst)
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return rest_modelform_factory(
            self.model,
            form=form_class,
            form_factory=smartmodelform_factory,
            resource_typemapper=self.resource_typemapper,
            auto_related_direct_fields=pyston_settings.AUTO_RELATED_DIRECT_FIELDS,
            auto_related_reverse_fields=pyston_settings.AUTO_RELATED_REVERSE_FIELDS,
            request=self.request,
            exclude=exclude,
            fields=fields,
            formfield_callback=self.formfield_for_dbfield,
            labels=self.get_field_labels()
        )


class ModelCoreResourceMixin(FieldPermissionViewMixin, CoreResourceMixin, PermissionsModelCoreResourceMixin):

    DEFAULT_REST_CONTEXT_MAPPING = {
        **BaseResource.DEFAULT_REST_CONTEXT_MAPPING,
        'request_count': ('HTTP_X_REQUEST_COUNT', '_request_count'),
        'direction': ('HTTP_X_DIRECTION', '_direction'),
        'order': ('HTTP_X_ORDER', '_order')
    }

    field_labels = None
    filters = {}

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def get_allowed_fields_rfs(self, obj=None):
        return super().get_allowed_fields_rfs().subtract(self._get_disallowed_fields_from_permissions(obj=obj))

    def get_fields(self, obj=None):
        fields = list(self.fields) if self.fields is not None else None
        return self.core.get_rest_fields(self.request, obj=None) if fields is None else fields

    def get_default_fields(self, obj=None):
        default_fields = list(self.default_fields) if self.default_fields is not None else None
        return self.core.get_rest_default_fields(self.request, obj=None) if default_fields is None else default_fields

    def get_detailed_fields(self, obj=None):
        detailed_fields = list(self.detailed_fields) if self.detailed_fields is not None else self.get_fields(obj=obj)
        return self.core.get_rest_detailed_fields(self.request, obj=obj) if detailed_fields is None else detailed_fields

    def get_general_fields(self, obj=None):
        general_fields = list(self.general_fields) if self.general_fields is not None else self.get_fields(obj=obj)
        return self.core.get_rest_general_fields(self.request, obj=obj) if general_fields is None else general_fields

    def get_guest_fields(self, obj=None):
        guest_fields = list(self.guest_fields) if self.guest_fields is not None else None
        return self.core.get_rest_guest_fields(self.request, obj=obj) if guest_fields is None else guest_fields

    def get_extra_fields(self, obj=None):
        extra_fields = list(self.extra_fields) if self.extra_fields is not None else None
        return self.core.get_rest_extra_fields(self.request) if extra_fields is None else extra_fields

    def get_extra_filter_fields(self):
        extra_filter_fields = list(self.extra_filter_fields) if self.extra_filter_fields is not None else None
        return (
            self.core.get_rest_extra_filter_fields(self.request) if extra_filter_fields is None else extra_filter_fields
        )

    def get_filter_fields(self):
        filter_fields = list(self.filter_fields) if self.filter_fields is not None else None
        return self.core.get_rest_filter_fields(self.request) if filter_fields is None else filter_fields

    def get_extra_order_fields(self):
        extra_order_fields = list(self.extra_order_fields) if self.extra_order_fields is not None else None
        return self.core.get_rest_extra_order_fields(self.request) if extra_order_fields is None else extra_order_fields

    def get_order_fields(self):
        order_fields = list(self.order_fields) if self.order_fields is not None else None
        return self.core.get_rest_order_fields(self.request) if order_fields is None else order_fields

    def get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None else self.core.get_rest_field_labels(self.request)
        )

    def get_field_label(self, field_name):
        return get_field_label_from_path(
            self.model,
            (
                field_name[:-len(LOOKUP_SEP + METHOD_OBJ_STR_NAME)]
                if field_name.endswith(LOOKUP_SEP + METHOD_OBJ_STR_NAME)
                else field_name
            ),
            field_labels=self.get_field_labels()
        )

    def _get_exclude(self, obj=None):
        return (
            list(self.core.get_rest_form_exclude(self.request, obj))
            + list(self._get_readonly_fields_from_permissions(obj))
        )


class DjangoCoreResource(ModelCoreResourceMixin, SmartFormDjangoResource):

    form_class = None
    abstract = True
    filter_manager = CoreDjangoFilterManager()

    def _preload_queryset(self, qs):
        return self.core.preload_queryset(self.request, qs)

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

    def put(self):
        # TODO: backward compatibility for bulk update should be used only patch
        return super().put() if self.kwargs.get(self.pk_name) else self.update_bulk()

    def patch(self):
        return super().patch() if self.kwargs.get(self.pk_name) else self.update_bulk()

    @transaction.smart_atomic
    def update_bulk(self):
        qs = self._filter_queryset(self._get_queryset())
        BULK_CHANGE_LIMIT = getattr(django_settings, 'BULK_CHANGE_LIMIT', 200)
        if qs.count() > BULK_CHANGE_LIMIT:
            return RestErrorResponse(
                msg=ugettext('Only %s objects can be changed by one request').format(BULK_CHANGE_LIMIT),
                code=413)

        data = self.get_dict_data()
        objects, errors = zip(*(self._update_obj(obj, data) for obj in qs))
        compact_errors = tuple(err for err in errors if err)
        return RestErrorsResponse(compact_errors) if len(compact_errors) > 0 else objects

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
        except RestException as ex:
            return (None, self._format_message(obj, ex))

    def _format_message(self, obj, ex):
        return {
            'id': obj.pk,
            'errors': {k: mark_safe(force_text(v)) for k, v in ex.errors.items()} if hasattr(ex, 'errors') else {},
            '_obj_name': force_text(obj),
        }
