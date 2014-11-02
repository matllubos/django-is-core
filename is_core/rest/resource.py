from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import NoReverseMatch
from django.http.response import Http404
from django.utils.encoding import force_text

from piston.resource import BaseResource, BaseModelResource
from piston.utils import get_object_or_none
from piston.exception import (RestException, MimerDataException, NotAllowedException, UnsupportedMediaTypeException,
                              ResourceNotFoundException, NotAllowedMethodException, DuplicateEntryException,
                              ConflictException)

from is_core.filters import get_model_field_or_method_filter
from is_core.patterns import RestPattern, patterns
from is_core.utils.decorators import classproperty
from is_core.exceptions import HttpForbiddenResponseException
from is_core.exceptions.response import (HttpBadRequestResponseException, HttpUnsupportedMediaTypeResponseException,
                                         HttpMethodNotAllowedResponseException, HttpDuplicateResponseException)


class RestResource(BaseResource):
    login_required = True
    register = False

    @classproperty
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

    fields = ('id', '_rest_links', '_actions', '_class_names', '_obj_name')
    default_detailed_fields = ('id', '_rest_links', '_obj_name')
    default_general_fields = ('id', '_rest_links', '_obj_name')
    form_class = None

    def get_fields(self, obj=None):
        return self.core.get_rest_fields(self.request, obj=obj)

    def get_default_detailed_fields(self, obj=None):
        return self.core.get_rest_detailed_fields(self.request, obj=obj)

    def get_default_general_fields(self, obj=None):
        return self.core.get_rest_general_fields(self.request)

    def get_guest_fields(self, request):
        return self.core.get_rest_guest_fields(request)

    def _web_links(self, obj):
        web_links = {}
        for pattern in self.core.web_link_patterns(self.request):
            if pattern.send_in_rest:
                url = pattern.get_url_string(self.request, obj=obj)
                if url:
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
        ac = self.core.get_list_actions(self.request, obj)
        return ac

    def _class_names(self, obj):
        return self.core.get_rest_obj_class_names(self.request, obj)

    def get_queryset(self):
        return self.core.get_queryset(self.request)

    def _filter_queryset(self, qs):
        filter_terms = self.request.GET.dict()

        for filter_term, filter_val in filter_terms.items():
            try:
                if not filter_term.startswith('_'):
                    filter = get_model_field_or_method_filter(filter_term, self.model, filter_val)
                    qs = filter.filter_queryset(qs, self.request)
                    force_text(qs.query)
            except:
                raise RestException(_('Cannot resolve filter "%s"') % filter_term)

        return qs

    def _order_by(self, qs, order_field):
        dir = self.request.META.get('HTTP_X_DIRECTION', 'ASC')

        if dir.upper() == 'DESC':
            order_field = '-' + order_field
        return qs.order_by(order_field)

    def _order_queryset(self, qs):
        if not 'HTTP_X_ORDER' in self.request.META:
            return qs
        order_field = self.request.META.get('HTTP_X_ORDER')
        qs = self._order_by(qs, order_field)
        try:
            # Queryset validation, there is no other option
            force_text(qs.query)
        except Exception as ex:
            raise RestException(_('Cannot resolve X-Order value "%s" into field') % order_field)
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
