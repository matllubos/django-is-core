from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch
from django.http.response import Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.encoding import force_text

from pyston.exception import (RESTException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException, DataInvalidException)
from pyston.resource import BaseResource, BaseModelResource, DefaultRESTModelResource
from pyston.response import RESTErrorResponse, RESTErrorsResponse
from pyston.utils import rfs

from chamber.shortcuts import get_object_or_none
from chamber.utils.decorators import classproperty
from chamber.utils import transaction

from is_core.config import settings
from is_core.exceptions.response import (HTTPBadRequestResponseException, HTTPUnsupportedMediaTypeResponseException,
                                         HTTPMethodNotAllowedResponseException, HTTPDuplicateResponseException,
                                         HTTPForbiddenResponseException, HTTPUnauthorizedResponseException)
from is_core.filters import get_model_field_or_method_filter, FilterException, FilterValueException
from is_core.forms.models import smartmodelform_factory
from is_core.patterns import RESTPattern, patterns
from is_core.utils.immutable import merge


class RESTLoginMixin(object):

    login_required = True
    login_post_required = True
    login_put_required = True
    login_get_required = True
    login_delete_required = True
    login_head_required = True
    login_options_required = True

    def has_login_post_required(self):
        return self.login_required and self.login_post_required

    def has_login_put_required(self):
        return self.login_required and self.login_put_required

    def has_login_get_required(self):
        return self.login_required and self.login_get_required

    def has_login_delete_required(self):
        return self.login_required and self.login_delete_required

    def has_login_head_required(self):
        return self.login_required and self.login_head_required and self.has_login_get_required()

    def has_login_options_required(self):
        return self.login_required and self.login_options_required

    def dispatch(self, request, *args, **kwargs):
        if ((not hasattr(request, 'user') or not request.user or not request.user.is_authenticated()) and
                getattr(self, 'has_login_{}_required'.format(request.method.lower()))()):
            raise HTTPUnauthorizedResponseException
        else:
            return super(RESTLoginMixin, self).dispatch(request, *args, **kwargs)


class RESTResource(RESTLoginMixin, BaseResource):

    register = False
    abstract = True

    @classproperty
    @classmethod
    def csrf_exempt(cls):
        return not cls.login_required

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'core'):
            self.core.init_rest_request(request)
        return super(RESTResource, self).dispatch(request, *args, **kwargs)

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
        return super(RESTResource, self)._get_error_response(exception)

    def _get_cors_allowed_headers(self):
        return super(RESTResource, self)._get_cors_allowed_headers() + (settings.AUTH_HEADER_NAME,)


class RESTModelCoreResourcePermissionsMixin(object):

    pk_name = 'pk'

    def has_get_permission(self, obj=None, **kwargs):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.has_login_get_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_get_permission(obj=obj, **kwargs) and
                self.core.has_rest_read_permission(self.request, obj=obj, **kwargs))

    def has_post_permission(self, obj=None, **kwargs):
        return ((not self.has_login_post_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_post_permission(obj=obj, **kwargs) and
                self.core.has_rest_create_permission(self.request, obj=obj, **kwargs))

    def has_put_permission(self, obj=None, **kwargs):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.has_login_put_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_put_permission(obj=obj, **kwargs) and
                self.core.has_rest_update_permission(self.request, obj=obj, **kwargs))

    def has_delete_permission(self, obj=None, **kwargs):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.has_login_delete_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_delete_permission(obj=obj, **kwargs) and
                self.core.has_rest_delete_permission(self.request, obj=obj, **kwargs))

    def has_head_permission(self, obj=None, **kwargs):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.has_login_head_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_head_permission(obj=obj, **kwargs) and
                self.core.has_rest_read_permission(self.request, obj=obj, **kwargs))

    def has_options_permission(self, obj=None, **kwargs):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.has_login_options_required() or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_options_permission(obj=obj, **kwargs) and
                self.core.has_rest_read_permission(self.request, obj=obj, **kwargs))

    def _get_perm_obj_or_none(self, pk=None):
        pk = pk or self.kwargs.get(self.pk_name)
        if pk:
            return get_object_or_none(self.core.model, pk=pk)
        else:
            return None


class RESTModelCoreMixin(RESTModelCoreResourcePermissionsMixin):

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_obj_or_none(self, pk=None):
        return get_object_or_none(self._get_queryset(), pk=(pk or self.kwargs.get(self.pk_name)))

    def _get_obj_or_404(self, pk=None):
        obj = self._get_obj_or_none(pk)
        if not obj:
            raise Http404
        return obj


class EntryPointResource(RESTResource):

    login_required = False
    allowed_methods = ('get', 'head', 'options')

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


class RESTModelResource(RESTModelCoreMixin, RESTResource, BaseModelResource):

    form_class = None
    field_labels = None
    abstract = True
    filters = {}
    default_fields_extension = ('_rest_links',)

    def _get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None else self.core.get_rest_form_field_labels(self.request)
        )

    def get_fields(self):
        fields = super(DefaultRESTModelResource, self).get_fields()
        return self.core.get_rest_fields(self.request) if fields is None else fields

    def get_detailed_fields(self):
        detailed_fields = super(DefaultRESTModelResource, self).get_detailed_fields()
        return self.core.get_rest_detailed_fields(self.request) if detailed_fields is None else detailed_fields

    def get_general_fields(self):
        general_fields = super(DefaultRESTModelResource, self).get_general_fields()
        return self.core.get_rest_general_fields(self.request) if general_fields is None else general_fields

    def get_guest_fields(self, obj=None):
        guest_fields = super(DefaultRESTModelResource, self).get_guest_fields()
        return self.core.get_rest_guest_fields(self.request, obj=obj) if guest_fields is None else guest_fields

    def get_extra_fields(self):
        extra_fields = super(DefaultRESTModelResource, self).get_extra_fields()
        return self.core.get_rest_extra_fields(self.request) if extra_fields is None else extra_fields

    def get_default_fields(self):
        default_fields = super(DefaultRESTModelResource, self).get_default_fields()
        return self.core.get_rest_default_fields(self.request) if default_fields is None else default_fields

    def get_default_fields_rfs(self):
        return super(RESTModelResource, self).get_default_fields_rfs().join(rfs(self.default_fields_extension))

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

    def _get_filter(self, filter_term):
        filter_name = filter_term.split('__')[0]

        if filter_name in self.filters:
            return self.filters[filter_name](filter_term, filter_term)
        else:
            return get_model_field_or_method_filter(filter_term, self.model)

    def _filter_queryset(self, qs):
        filter_terms_with_values = [
            (filter_term, value) for filter_term, value in self.request.GET.dict().items()
            if not filter_term.startswith('_')
        ]
        qs_filter_terms = []
        for filter_term, value in filter_terms_with_values:
            try:
                q = self._get_filter(filter_term).get_q(value, self.request)
                qs_filter_terms.append(q)
            except FilterValueException as ex:
                raise RESTException(
                    mark_safe(ugettext('Invalid filter value "{}={}". {}').format(filter_term, value, ex))
                )
            except FilterException:
                raise RESTException(mark_safe(ugettext('Cannot resolve filter "{}={}"').format(filter_term, value)))

        return qs.filter(pk__in=qs.filter(*qs_filter_terms).values('pk')) if qs_filter_terms else qs

    def _order_queryset(self, qs):
        if 'order' not in self.request._rest_context:
            return qs
        order_field = self.request._rest_context.get('order')
        try:
            qs = qs.order_by(*order_field.split(','))
            # Queryset validation, there is no other option
            force_text(qs.query)
        except Exception:
            raise RESTException(mark_safe(ugettext('Cannot resolve Order value "%s" into fields') % order_field))
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
        return super(RESTModelResource, self).put() if self.kwargs.get(self.pk_name) else self.update_bulk()

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
            return (self._create_or_update(merge(data, {self.pk_field_name: obj.pk})), None)
        except DataInvalidException as ex:
            return (None, self._format_message(obj, ex))
        except (ConflictException, NotAllowedException):
            raise
        except RESTException as ex:
            return (None, self._format_message(obj, ex))

    def _extract_message(self, ex):
        return '\n'.join(ex.errors.values()) if hasattr(ex, 'errors') else ex.message

    def _format_message(self, obj, ex):
        return {
            'id': obj.pk,
            'errors': {k: mark_safe(v) for k, v in ex.errors.items()} if hasattr(ex, 'errors') else {},
            '_obj_name': mark_safe(''.join(('#', str(obj.pk), ' ', self._extract_message(ex)))),
        }


class UIRESTModelResource(RESTModelResource):

    def _web_links(self, obj):
        web_links = {}
        for pattern in self.core.web_link_patterns(self.request):
            if pattern.send_in_rest:
                url = pattern.get_url_string(self.request, obj=obj)
                if url and pattern.can_call_get(self.request, obj=obj):
                    web_links[pattern.name] = url
        return web_links

    def _class_names(self, obj):
        return self.core.get_rest_obj_class_names(self.request, obj)

