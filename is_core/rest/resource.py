from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch
from django.db import transaction
from django.http.response import Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from piston.exception import (RestException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException, DataInvalidException)
from piston.resource import BaseResource, BaseModelResource
from piston.response import RestErrorResponse, RestErrorsResponse

from chamber.shortcuts import get_object_or_none
from chamber.utils.decorators import classproperty

from is_core.exceptions import HttpForbiddenResponseException
from is_core.exceptions.response import (HttpBadRequestResponseException, HttpUnsupportedMediaTypeResponseException,
                                         HttpMethodNotAllowedResponseException, HttpDuplicateResponseException)
from is_core.filters import get_model_field_or_method_filter
from is_core.forms.models import smartmodelform_factory
from is_core.patterns import RestPattern, patterns
from is_core.utils.immutable import merge


class RestResource(BaseResource):
    login_required = True
    register = False

    @classproperty
    @classmethod
    def csrf_exempt(cls):
        return not cls.login_required

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'core'):
            self.core.init_rest_request(request)
        return super(RestResource, self).dispatch(request, *args, **kwargs)

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    def _get_error_response(self, exception):
        """
        Trasform piston exceptions to Is-core exceptions and raise it
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
        return super(RestResource, self)._get_error_response(exception)


class RestModelCoreResourcePermissionsMixin(object):

    pk_name = 'pk'

    def has_get_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RestModelCoreResourcePermissionsMixin, self).has_get_permission(obj) and
                self.core.has_rest_read_permission(self.request, obj, via))

    def has_post_permission(self, obj=None, via=None):
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RestModelCoreResourcePermissionsMixin, self).has_post_permission(obj) and
                self.core.has_rest_create_permission(self.request, obj, via))

    def has_put_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RestModelCoreResourcePermissionsMixin, self).has_put_permission(obj) and
                self.core.has_rest_update_permission(self.request, obj, via))

    def has_delete_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RestModelCoreResourcePermissionsMixin, self).has_delete_permission(obj) and
                self.core.has_rest_delete_permission(self.request, obj, via))

    def _get_perm_obj_or_none(self, pk=None):
        pk = pk or self.kwargs.get(self.pk_name)
        if pk:
            return get_object_or_none(self.core.model, pk=pk)
        else:
            return None


class RestModelCoreMixin(RestModelCoreResourcePermissionsMixin):

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_obj_or_none(self, pk=None):
        return get_object_or_none(self._get_queryset(), pk=(pk or self.kwargs.get(self.pk_name)))

    def _get_obj_or_404(self, pk=None):
        obj = self._get_obj_or_none(pk)
        if not obj:
            raise Http404
        return obj


class EntryPointResource(RestResource):
    login_required = False
    allowed_methods = ('get',)

    def read(self):
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


class RestModelResource(RestModelCoreMixin, RestResource, BaseModelResource):

    default_detailed_fields = ('id', '_rest_links', '_obj_name')
    default_general_fields = ('id', '_rest_links', '_obj_name')
    form_class = None
    field_labels = None

    def _get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None else self.core.get_rest_form_field_labels(self.request)
        )

    def get_extra_fields(self, obj=None):
        return self.core.get_rest_extra_fields(self.request, obj=obj)

    def get_default_detailed_fields(self, obj=None):
        return self.core.get_rest_detailed_fields(self.request, obj=obj)

    def get_default_general_fields(self, obj=None):
        return self.core.get_rest_general_fields(self.request, obj=obj)

    def get_guest_fields(self, obj=None):
        return self.core.get_rest_guest_fields(self.request, obj=obj)

    def _web_links(self, obj):
        web_links = {}
        for pattern in self.core.web_link_patterns(self.request):
            if pattern.send_in_rest:
                url = pattern.get_url_string(self.request, obj=obj)
                if url and pattern.can_call_get(self.request, obj=obj):
                    web_links[pattern.name] = url
        return web_links

    def _rest_links(self, obj):
        rest_links = {}
        for pattern in self.core.resource_patterns.values():
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
        mapping = super(RestModelResource, self)._get_headers_queryset_context_mapping()
        mapping.update({
            'direction': ('HTTP_X_DIRECTION', '_direction'),
            'order': ('HTTP_X_ORDER', '_order')
        })
        return mapping

    def _preload_queryset(self, qs):
        return self.core.preload_queryset(self.request, qs)

    def _filter_queryset(self, qs):
        filter_terms = self.request.GET.dict()

        for filter_term, filter_val in filter_terms.items():
            if not filter_term.startswith('_'):
                try:
                    filter = get_model_field_or_method_filter(filter_term, self.model, filter_val)
                    qs = filter.filter_queryset(qs, self.request)
                except:
                    raise RestException(mark_safe(ugettext('Cannot resolve filter "%s"') % filter_term))

        return qs

    def _order_queryset(self, qs):
        if 'order' not in self.request._rest_context:
            return qs
        order_field = self.request._rest_context.get('order')
        try:
            qs = qs.order_by(*order_field.split(','))
            # Queryset validation, there is no other option
            unicode(qs.query)
        except Exception:
            raise RestException(mark_safe(ugettext('Cannot resolve Order value "%s" into fields') % order_field))
        return qs

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
        return smartmodelform_factory(self.model, self.request, form=form_class, exclude=exclude, fields=fields,
                                      labels=self._get_field_labels())

    def put(self):
        return super(RestModelResource, self).put() if self.kwargs.get(self.pk_name) else self.update_bulk()

    @transaction.atomic
    def update_bulk(self):
        qs = self._filter_queryset(self.core.get_queryset(self.request))
        BULK_CHANGE_LIMIT = getattr(settings, 'BULK_CHANGE_LIMIT', 200)
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
            return (self._create_or_update(merge(data, {self.pk_field_name: obj.pk})), None)
        except DataInvalidException as ex:
            return (None, self._format_message(obj, ex))
        except (ConflictException, NotAllowedException):
            raise
        except RestException as ex:
            return (None, self._format_message(obj, ex))

    def _extract_message(self, ex):
        return '\n'.join(ex.errors.values()) if hasattr(ex, 'errors') else ex.message

    def _format_message(self, obj, ex):
        return {
            'id': obj.pk,
            'errors': {k: mark_safe(v) for k, v in ex.errors.items()} if hasattr(ex, 'errors') else {},
            '_obj_name': mark_safe(''.join(('#', str(obj.pk), ' ', self._extract_message(ex)))),
        }
