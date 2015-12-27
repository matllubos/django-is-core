from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as ugettext
from django.core.urlresolvers import NoReverseMatch
from django.http.response import Http404
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from piston.resource import BaseResource, BaseModelResource
from piston.exception import (RESTException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException)

from chamber.shortcuts import get_object_or_none

from is_core.filters import get_model_field_or_method_filter
from is_core.patterns import RESTPattern, patterns
from is_core.exceptions import HttpForbiddenResponseException
from is_core.exceptions.response import (HttpBadRequestResponseException, HttpUnsupportedMediaTypeResponseException,
                                         HttpMethodNotAllowedResponseException, HttpDuplicateResponseException)
from is_core.forms.models import smartmodelform_factory
from is_core import config

from chamber.utils.decorators import classproperty


class RESTResource(BaseResource):
    login_required = True
    register = False

    @classproperty
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
        return super(RESTResource, self)._get_error_response(exception)

    def _get_cors_allowed_headers(self):
        return super(RESTResource, self)._get_cors_allowed_headers() + (config.IS_CORE_AUTH_HEADER_NAME,)


class RESTModelCoreResourcePermissionsMixin(object):

    pk_name = 'pk'

    def has_get_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_get_permission(obj) and
                self.core.has_rest_read_permission(self.request, obj, via))

    def has_post_permission(self, obj=None, via=None):
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_post_permission(obj) and
                self.core.has_rest_create_permission(self.request, obj, via))

    def has_put_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_put_permission(obj) and
                self.core.has_rest_update_permission(self.request, obj, via))

    def has_delete_permission(self, obj=None, via=None):
        obj = obj or self._get_perm_obj_or_none()
        return ((not self.login_required or self.request.user.is_authenticated()) and
                super(RESTModelCoreResourcePermissionsMixin, self).has_delete_permission(obj) and
                self.core.has_rest_delete_permission(self.request, obj, via))

    def _get_perm_obj_or_none(self, pk=None):
        pk = pk or self._get_pk()
        if pk:
            return get_object_or_none(self.core.model, pk=pk)
        else:
            return None


class RESTModelCoreMixin(RESTModelCoreResourcePermissionsMixin):

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_obj_or_none(self, pk=None):
        return get_object_or_none(self._get_queryset(), pk=(pk or self._get_pk()))

    def _get_obj_or_404(self, pk=None):
        obj = self._get_obj_or_none(pk)
        if not obj:
            raise Http404
        return obj


class EntryPointResource(RESTResource):
    login_required = False
    allowed_methods = ('get',)

    def read(self):
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

    default_detailed_fields = ('id', '_rest_links', '_obj_name')
    default_general_fields = ('id', '_rest_links', '_obj_name')
    form_class = None

    def get_extra_fields(self, obj=None):
        return self.core.get_rest_extra_fields(self.request, obj=obj)

    def get_default_detailed_fields(self, obj=None):
        return self.core.get_rest_detailed_fields(self.request, obj=obj)

    def get_default_general_fields(self, obj=None):
        return self.core.get_rest_general_fields(self.request, obj=obj)

    def get_guest_fields(self, obj=None):
        return self.core.get_rest_guest_fields(self.request, obj=obj)

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
        ac = self.core.get_list_actions(self.request, obj)
        return ac

    def get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_headers_queryset_context_mapping(self):
        mapping = super(RESTModelResource, self)._get_headers_queryset_context_mapping()
        mapping.update({'order': ('HTTP_X_ORDER', '_order')})
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
                    raise RESTException(mark_safe(ugettext('Cannot resolve filter "%s"') % filter_term))

        return qs

    def _order_queryset(self, qs):
        if 'order' not in self.request._rest_context:
            return qs
        order_field = self.request._rest_context.get('order')
        try:
            qs = qs.order_by(*order_field.split(','))
            # Queryset validation, there is no other option
            force_text(qs.query)
        except:
            raise RESTException(mark_safe(ugettext('Cannot resolve Order value "%s" into fields') % order_field))
        return qs

    def _get_exclude(self, obj=None):
        return self.core.get_rest_form_exclude(self.request, obj)

    def _get_form_fields(self, obj=None):
        return self.core.get_rest_form_fields(self.request, obj)

    def _get_form_class(self, obj=None):
        return self.form_class or self.core.get_rest_form_class(self.request, obj)

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
        return smartmodelform_factory(self.model, self.request, form=form_class, exclude=exclude, fields=fields)

    def _get_cors_allowed_headers(self):
        return super(RESTModelResource, self)._get_cors_allowed_headers() + ('X-Order',)


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