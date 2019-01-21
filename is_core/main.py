"""
Core of django-is-core.
Contains controller added between model and UI/REST.
"""
import sys

from collections import OrderedDict

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.http.response import Http404
from django.core.exceptions import ValidationError
from django.forms.models import _get_foreign_key
from django.utils.functional import cached_property

from is_core.config import settings
from is_core.actions import WebAction, ConfirmRESTAction
from is_core.generic_views.form_views import AddModelFormView, DetailModelFormView, BulkChangeFormView
from is_core.generic_views.table_views import TableView
from is_core.rest.resource import RESTModelResource, UIRESTModelResource
from is_core.patterns import UIPattern, RESTPattern, DoubleRESTPattern, HiddenRESTPattern
from is_core.utils import flatten_fieldsets, str_to_class
from is_core.utils.compatibility import urls_wrapper, get_model_name, reverse
from is_core.menu import LinkMenuItem
from is_core.loading import register_core
from is_core.rest.factory import modelrest_factory
from is_core.forms.models import SmartModelForm

from .auth.permissions import PermissionsSet, IsAdminUser


class ISCoreBase(type):
    """Metaclass for IS core classes. Its main purpose is automatic registration cores to your application."""

    def __new__(cls, *args, **kwargs):
        name, _, attrs = args

        abstract = attrs.pop('abstract', False)
        super_new = super(ISCoreBase, cls).__new__
        new_class = super_new(cls, *args, **kwargs)
        model_module = sys.modules[new_class.__module__]
        app_label = model_module.__name__.split('.')[-2]

        if name != 'NewBase' and not abstract and new_class.register:
            register_core(app_label, new_class)
        return new_class


class ISCore(metaclass=ISCoreBase):
    """
    Parent of all IS cores. Contains common methods for all cores.
    This class is abstract.
    """

    abstract = True
    register = True

    verbose_name = None
    verbose_name_plural = None
    menu_group = None

    can_create = False
    can_read = True
    can_update = False
    can_delete = False

    default_permission = IsAdminUser()

    permission = None

    def __init__(self, site_name, menu_parent_groups):
        self.site_name = site_name
        self.menu_parent_groups = menu_parent_groups
        self.permission = self._init_permission(self.permission)

    def _init_permission(self, permission):
        return self._generate_permission_set() if permission is None else permission

    def _get_default_permission(self, name):
        return self.default_permission

    def _generate_permission_set(self):
        permission_dict = {}
      
        for permission_name in ('create', 'read', 'update', 'delete'):
            if getattr(self, 'can_{}'.format(permission_name)):
                permission_dict[permission_name] = self._get_default_permission(permission_name)
        return PermissionsSet(**permission_dict)

    def init_request(self, request):
        pass

    def get_urlpatterns(self, patterns):
        urls = []
        for pattern in patterns.values():
            url = pattern.get_url()
            if url:
                urls.append(url)

        return urls_wrapper(*urls)

    def get_urls(self):
        return ()

    def get_views(self):
        return {}

    def get_menu_groups(self):
        menu_groups = list(self.menu_parent_groups)
        if self.menu_group:
            menu_groups += (self.menu_group,)
        return menu_groups

    def get_url_prefix(self):
        return '/'.join(self.get_menu_groups())

    def get_menu_group_pattern_name(self):
        return '-'.join(self.get_menu_groups())


class ModelISCore(ISCore):
    """
    Parent of REST and UI cores that works as controller to specific model.
    This class is abstract.
    """

    abstract = True

    list_actions = ()

    # form params
    form_fields = None
    form_exclude = ()
    form_class = SmartModelForm
    form_edit_class = None
    form_add_class = None

    default_ordering = None

    field_labels = {}

    can_read = True
    can_create = True
    can_update = True
    can_delete = True

    def get_form_class(self, request, obj=None):
        return self.form_class

    def get_form_edit_class(self, request, obj=None):
        return self.form_edit_class or self.get_form_class(request, obj)

    def get_form_add_class(self, request, obj=None):
        return self.form_add_class or self.get_form_class(request, obj)

    def get_form_fields(self, request, obj=None):
        return self.form_fields

    def get_form_exclude(self, request, obj=None):
        return self.form_exclude

    def get_field_labels(self, request):
        return self.field_labels

    def pre_save_model(self, request, obj, form, change):
        pass

    def save_model(self, request, obj, form, change):
        obj.save()

    def post_save_model(self, request, obj, form, change):
        pass

    def pre_delete_model(self, request, obj):
        pass

    def delete_model(self, request, obj):
        obj.delete()

    def post_delete_model(self, request, obj):
        pass

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    @property
    def menu_group(self):
        return get_model_name(self.model)

    # TODO: remove this function
    def get_obj(self, request, **filters):
        try:
            return get_object_or_404(self.get_queryset(request), **filters)
        except (ValidationError, ValueError):
            raise Http404

    def get_default_ordering(self):
        return self.default_ordering if self.default_ordering is not None else (self.model._meta.ordering or ('pk',))

    def get_queryset(self, request):
        return self.model._default_manager.get_queryset().order_by(*self.get_default_ordering())

    def preload_queryset(self, request, qs):
        return qs

    def get_list_actions(self, request, obj):
        return list(self.list_actions)

    def get_default_action(self, request, obj):
        return None


class UIISCore(ISCore):
    """Main core for UI views."""

    abstract = True

    show_in_menu = True
    menu_url_name = None
    view_classes = ()
    default_ui_pattern_class = UIPattern

    def init_ui_request(self, request):
        self.init_request(request)

    def get_view_classes(self):
        return list(self.view_classes)

    @cached_property
    def ui_patterns(self):
        return self.get_ui_patterns()

    def get_ui_patterns(self):
        ui_patterns = OrderedDict()
        for view_class_definition in self.get_view_classes():
            name, view_vals = (view_class_definition[0], view_class_definition[1:])
            if name not in ui_patterns:
                if len(view_vals) == 3:
                    pattern, view, ViewPatternClass = view_vals
                else:
                    pattern, view = view_vals
                    ViewPatternClass = self.default_ui_pattern_class

                if isinstance(view, str):
                    view = getattr(self, view)()

                pattern_names = [name]
                group_pattern_name = self.get_menu_group_pattern_name()
                if group_pattern_name:
                    pattern_names += [self.get_menu_group_pattern_name()]

                ui_patterns[name] = ViewPatternClass('-'.join(pattern_names), self.site_name, pattern, view, self)
        return ui_patterns

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return (
            self.show_in_menu and self.menu_url_name and self.menu_url_name in self.ui_patterns and
            self.ui_patterns.get(self.menu_url_name).has_permission('get', request)
        )

    def is_active_menu_item(self, request, active_group):
        return active_group == self.menu_group

    def get_menu_item(self, request, active_group, item_class=LinkMenuItem):
        if self.get_show_in_menu(request):
            return item_class(self.verbose_name_plural, self.menu_url(request),
                              self.menu_group, self.is_active_menu_item(request, active_group))

    def menu_url(self, request):
        return self.ui_patterns.get(self.menu_url_name).get_url_string(request)


class RESTISCore(ISCore):
    """Main core for REST views."""

    rest_classes = ()
    default_rest_pattern_class = RESTPattern
    abstract = True

    api_url_name = None

    def init_rest_request(self, request):
        self.init_request(request)

    def get_rest_classes(self):
        return list(self.rest_classes)

    @cached_property
    def rest_patterns(self):
        return self.get_rest_patterns()

    def get_rest_patterns(self):
        rest_patterns = OrderedDict()
        for rest_class_definition in self.get_rest_classes():
            name, rest_vals = (rest_class_definition[0], rest_class_definition[1:])
            if name not in rest_patterns:
                if len(rest_vals) == 3:
                    pattern, rest, RESTPatternClass = rest_vals
                else:
                    pattern, rest = rest_vals
                    RESTPatternClass = self.default_rest_pattern_class

                if isinstance(rest, str):
                    rest = getattr(self, rest)()

                pattern_names = [name]
                group_pattern_name = self.get_menu_group_pattern_name()
                if group_pattern_name:
                    pattern_names += [self.get_menu_group_pattern_name()]
                rest_patterns[name] = RESTPatternClass('-'.join(pattern_names), self.site_name, pattern, rest, self)
        return rest_patterns

    def get_urls(self):
        return self.get_urlpatterns(self.rest_patterns)

    def get_api_url(self, request):
        return reverse(self.get_api_url_name())

    def get_api_url_name(self):
        return self.api_url_name or '{}:api-{}'.format(self.site_name, self.get_menu_group_pattern_name())

    def get_api_detail_url_name(self):
        return self.api_url_name or '{}:api-resource-{}'.format(self.site_name, self.get_menu_group_pattern_name())


class UIRESTISCoreMixin:
    """Helper that joins urls generated wit REST core and UI core."""

    def get_urls(self):
        return self.get_urlpatterns(self.rest_patterns) + self.get_urlpatterns(self.ui_patterns)


class UIRESTISCore(UIRESTISCoreMixin, UIISCore, RESTISCore):
    """UI REST Core, its main purpose is create custom REST resources and UI views."""

    abstract = True


class HomeUIISCore(UIISCore):

    menu_url_name = 'index'
    verbose_name_plural = _('Home')
    menu_group = 'home'
    abstract = settings.HOME_CORE != 'is_core.main.HomeUIISCore'

    def get_view_classes(self):
        view_classes = super(HomeUIISCore, self).get_view_classes()
        view_classes.append(('index', r'', str_to_class(settings.HOME_VIEW)))
        return view_classes

    def menu_url(self, request):
        return '/'

    def get_url_prefix(self):
        return ''


class UIModelISCore(ModelISCore, UIISCore):
    """Main core controller for specific model that provides UI views for model management (add, edit, list)."""

    abstract = True

    menu_url_name = 'list'

    # list view params
    list_per_page = None
    detail_export_types = settings.EXPORT_TYPES
    default_list_filter = {}

    # add/edit view params
    form_fieldsets = None
    form_readonly_fields = ()
    form_inline_views = None

    ui_form_add_class = None
    ui_form_edit_class = None
    ui_form_field_labels = None
    ui_list_field_labels = None
    ui_list_fields = ('_obj_name',)
    ui_export_fields = ()
    ui_list_export_fields = None
    ui_detail_export_fields = None
    ui_export_types = settings.EXPORT_TYPES
    ui_list_export_types = None
    ui_detail_export_types = None
    ui_add_view = AddModelFormView
    ui_detail_view = DetailModelFormView
    ui_list_view = TableView

    bulk_change_url_name = None

    @cached_property
    def default_model_view_classes(self):
        default_model_view_classes = []
        if self.can_create:
            default_model_view_classes.append(('add', r'add/', self.get_ui_add_view()))
        if self.can_read or self.can_update:
            default_model_view_classes.append(('detail', r'(?P<pk>[-\w]+)/', self.get_ui_detail_view()))
        if self.can_read:
            default_model_view_classes.append(('list', r'', self.get_ui_list_view()))
        return default_model_view_classes

    def get_view_classes(self):
        view_classes = super(UIModelISCore, self).get_view_classes() + list(self.default_model_view_classes)
        if self.is_bulk_change_enabled():
            view_classes.append((self.get_bulk_change_url_name(), r'bulk-change/?', BulkChangeFormView))
        return view_classes

    def get_ui_add_view(self):
        return self.ui_add_view

    def get_ui_detail_view(self):
        return self.ui_detail_view

    def get_ui_list_view(self):
        return self.ui_list_view

    def get_ui_form_add_class(self, request, obj=None):
        return self.ui_form_add_class or self.get_form_add_class(request, obj)

    def get_ui_form_edit_class(self, request, obj=None):
        return self.ui_form_edit_class or self.get_form_edit_class(request, obj)

    def get_form_fieldsets(self, request, obj=None):
        return self.form_fieldsets

    def get_form_readonly_fields(self, request, obj=None):
        return self.form_readonly_fields

    def get_ui_form_fields(self, request, obj=None):
        return self.get_form_fields(request, obj)

    def get_ui_form_exclude(self, request, obj=None):
        return self.get_form_exclude(request, obj)

    def is_bulk_change_enabled(self):
        return self.get_bulk_change_url_name() is not None

    def get_bulk_change_url_name(self):
        return self.bulk_change_url_name

    def get_bulk_change_fields(self, request):
        return getattr(self, 'bulk_change_fields', ())

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return (
            self.menu_url_name in self.ui_patterns and self.show_in_menu and
            self.ui_patterns.get(self.menu_url_name).has_permission('get', request)
        )

    def get_form_inline_views(self, request, obj=None):
        return self.form_inline_views

    def get_default_list_filter(self, request):
        return self.default_list_filter.copy()

    def get_ui_list_fields(self, request):
        return list(self.ui_list_fields)

    def get_ui_export_fields(self, request):
        return list(self.ui_export_fields)

    def get_ui_list_export_fields(self, request):
        return (
            list(self.ui_list_export_fields) if self.ui_list_export_fields is not None
            else self.get_ui_export_fields(request)
        )

    def get_ui_detail_export_fields(self, request, obj=None):
        return (
            list(self.ui_detail_export_fields) if self.ui_detail_export_fields is not None
            else self.get_ui_export_fields(request)
        )

    def get_ui_export_types(self, request):
        return list(self.ui_export_types or ())

    def get_ui_list_export_types(self, request):
        return (
            list(self.ui_list_export_types) if self.ui_list_export_types is not None
            else self.get_ui_export_types(request)
        )

    def get_ui_detail_export_types(self, request):
        return (
            list(self.ui_detail_export_fields) if self.ui_detail_export_fields is not None
            else self.get_ui_export_types(request)
        )

    def get_list_per_page(self, request):
        return self.list_per_page

    def get_add_url(self, request):
        if 'add' in self.ui_patterns:
            return self.ui_patterns.get('add').get_url_string(request)

    def get_ui_form_field_labels(self, request):
        return self.ui_form_field_labels if self.ui_form_field_labels is not None else self.get_field_labels(request)

    def get_ui_list_field_labels(self, request):
        return self.ui_list_field_labels if self.ui_list_field_labels is not None else self.get_field_labels(request)

    def get_detail_export_types(self):
        return self.detail_export_types


class RESTModelISCore(RESTISCore, ModelISCore):
    """
    Main core controller for specific model that provides REST resources for model management.
    CRUD (POST, GET, PUT, DELETE).
    """

    abstract = True

    # Allowed rest fields
    rest_fields = None
    rest_extra_fields = None
    rest_detailed_fields = None
    rest_general_fields = None
    rest_guest_fields = None
    rest_default_fields = None
    rest_filter_fields = None
    rest_extra_filter_fields = None
    rest_order_fields = None
    rest_extra_order_fields = None

    rest_default_fields_extension = settings.REST_DEFAULT_FIELDS_EXTENSION

    rest_form_edit_class = None
    rest_form_add_class = None

    rest_resource_class = RESTModelResource
    rest_form_field_labels = None
    rest_paginator = None

    def get_rest_allowed_methods(self):
        rest_allowed_methods = ['options']
        if self.can_read:
            rest_allowed_methods += ['get', 'head']
        if self.can_update:
            rest_allowed_methods += ['put', 'patch']
        if self.can_create:
            rest_allowed_methods.append('post')
        if self.can_delete:
            rest_allowed_methods.append('delete')
        return rest_allowed_methods

    def get_rest_form_field_labels(self, request):
        return (
            self.rest_form_field_labels if self.rest_form_field_labels is not None
            else self.get_field_labels(request)
        )

    def get_rest_form_add_class(self, request, obj=None):
        return self.rest_form_add_class or self.get_form_add_class(request, obj)

    def get_rest_form_edit_class(self, request, obj=None):
        return self.rest_form_edit_class or self.get_form_edit_class(request, obj)

    def get_rest_form_fields(self, request, obj=None):
        return self.get_form_fields(request, obj)

    def get_rest_form_exclude(self, request, obj=None):
        return self.get_form_exclude(request, obj)

    def get_rest_default_fields_extension(self, request, obj=None):
        return list(self.rest_default_fields_extension)

    def get_rest_extra_fields(self, request, obj=None):
        return list(
            self.model._rest_meta.extra_fields if self.rest_extra_fields is None
            else self.rest_extra_fields
        )

    def get_rest_default_fields(self, request, obj=None):
        return list(
            self.model._rest_meta.default_fields if self.rest_default_fields is None
            else self.rest_default_fields
        )

    def get_rest_fields(self, request, obj=None):
        return self.rest_fields

    def get_rest_general_fields(self, request, obj=None):
        return list(
            self.model._rest_meta.general_fields if self.rest_general_fields is None
            else self.rest_general_fields
        )

    def get_rest_detailed_fields(self, request, obj=None):
        return list(
            self.model._rest_meta.detailed_fields if self.rest_detailed_fields is None
            else self.rest_detailed_fields
        )

    def get_rest_guest_fields(self, request, obj=None):
        return list(
            self.model._rest_meta.guest_fields if self.rest_guest_fields is None
            else self.rest_guest_fields
        )

    def get_rest_extra_filter_fields(self, request):
        return (
            self.model._rest_meta.extra_filter_fields if self.rest_extra_filter_fields is None
            else self.rest_extra_filter_fields
        )

    def get_rest_filter_fields(self, request):
        return (
            self.model._rest_meta.filter_fields if self.rest_filter_fields is None
            else self.rest_filter_fields
        )

    def get_rest_extra_order_fields(self, request):
        return (
            self.model._rest_meta.extra_order_fields if self.rest_extra_order_fields is None
            else self.rest_extra_order_fields
        )

    def get_rest_order_fields(self, request):
        return (
            self.model._rest_meta.order_fields if self.rest_order_fields is None
            else self.rest_order_fields
        )

    def get_rest_class(self):
        resource_kwargs = {}
        if self.rest_paginator:
            resource_kwargs['paginator'] = self.rest_paginator
        return modelrest_factory(self.model, self.rest_resource_class, resource_kwargs=resource_kwargs)

    def get_rest_patterns(self):
        rest_patterns = super(RESTModelISCore, self).get_rest_patterns()
        rest_patterns.update(DoubleRESTPattern(self.get_rest_class(), self.default_rest_pattern_class, self,
                                               self.get_rest_allowed_methods()).patterns)
        return rest_patterns

    def get_list_actions(self, request, obj):
        list_actions = super(RESTModelISCore, self).get_list_actions(request, obj)
        api_resource = self.rest_patterns.get('api-resource')
        if self.can_delete and api_resource.has_permission('delete', request, obj=obj):
            confirm_dialog = ConfirmRESTAction.ConfirmDialog(_('Do you really want to delete "%s"') % obj)
            list_actions.append(ConfirmRESTAction('api-resource-{}'.format(self.get_menu_group_pattern_name()),
                                                  _('Delete'), 'DELETE', confirm_dialog=confirm_dialog,
                                                  class_name='delete', success_text=_('Record "%s" was deleted') % obj))
        return list_actions


class UIRESTModelISCore(UIRESTISCoreMixin, RESTModelISCore, UIModelISCore):
    """
    Combination of UI views and REST resources. UI views uses REST resources for printing model data, filtering,
    paging and so on.
    """

    abstract = True
    ui_rest_extra_fields = ('_web_links', '_rest_links', '_default_action', '_actions', '_class_names', '_obj_name')
    rest_resource_class = UIRESTModelResource
    rest_obj_class_names = ()

    def get_rest_extra_fields(self, request, obj=None):
        return (
            super(UIRESTModelISCore, self).get_rest_extra_fields(request, obj) +
            list(self.get_ui_list_fields(request)) +
            list(self.get_ui_list_export_fields(request)) +
            list(self.get_ui_detail_export_fields(request)) +
            list(self.ui_rest_extra_fields)
        )

    def get_api_detail_url(self, request, obj):
        return reverse(self.get_api_detail_url_name(), kwargs={'pk': obj.pk})

    def get_rest_form_fields(self, request, obj=None):
        return flatten_fieldsets(self.get_form_fieldsets(request, obj) or ()) or self.get_form_fields(request, obj)

    def get_rest_form_exclude(self, request, obj=None):
        return self.get_form_readonly_fields(request, obj) + self.get_form_exclude(request, obj)

    def get_list_actions(self, request, obj):
        list_actions = super(UIRESTModelISCore, self).get_list_actions(request, obj)
        detail_pattern = self.ui_patterns.get('detail')
        if detail_pattern and detail_pattern.has_permission('get', request, obj=obj):
            return [
                WebAction(
                    'detail-{}'.format(self.get_menu_group_pattern_name()), _('Detail'),
                    'edit' if detail_pattern.has_permission('post', request, obj=obj) else 'detail'
                )
            ] + list(list_actions)
        else:
            return list_actions

    def get_default_action(self, request, obj):
        return 'detail-{}'.format(self.get_menu_group_pattern_name())

    def web_link_patterns(self, request):
        return self.ui_patterns.values()

    def get_rest_obj_class_names(self, request, obj):
        return list(self.rest_obj_class_names)
