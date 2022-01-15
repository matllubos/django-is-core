"""
Core of django-is-core.
Contains controller added between model and UI/REST.
"""
import sys

from copy import deepcopy

from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.urls import reverse

import import_string

from is_core.auth.permissions import FieldsSetPermission
from is_core.config import settings
from is_core.actions import WebAction, ConfirmRestAction
from is_core.generic_views.form_views import BulkChangeFormView
from is_core.generic_views.detail_views import DjangoDetailFormView
from is_core.generic_views.add_views import DjangoAddFormView
from is_core.generic_views.table_views import DjangoTableView
from is_core.rest.resource import DjangoCoreResource
from is_core.rest.paginators import DjangoOffsetBasedPaginator
from is_core.patterns import UiPattern, RestPattern, DoubleRestPattern
from is_core.utils import flatten_fieldsets, GetMethodFieldMixin, get_model_name, PK_PATTERN
from is_core.menu import LinkMenuItem
from is_core.loading import register_core
from is_core.rest.factory import modelrest_factory
from is_core.forms.models import SmartModelForm
from is_core.utils.decorators import short_description

from .auth.permissions import PermissionsSet, IsAdminUser


class CoreBase(type):
    """Metaclass for IS core classes. Its main purpose is automatic registration cores to your application."""

    def __new__(cls, *args, **kwargs):
        name, _, attrs = args

        abstract = attrs.pop('abstract', False)
        super_new = super(CoreBase, cls).__new__
        new_class = super_new(cls, *args, **kwargs)
        model_module = sys.modules[new_class.__module__]
        app_label = model_module.__name__.split('.')[-2]

        if name != 'NewBase' and not abstract and new_class.register:
            register_core(app_label, new_class)
        return new_class


class Core(metaclass=CoreBase):
    """
    Parent of all IS cores. Contains common methods for all cores.
    This class is abstract.
    """

    abstract = True
    register = True

    list_actions = ()

    menu_group = None

    can_create = False
    can_read = True
    can_update = False
    can_delete = False

    default_permission = IsAdminUser()

    permission = None
    field_permissions = FieldsSetPermission()

    verbose_name = None
    verbose_name_plural = None

    def __init__(self, site_name, menu_parent_groups):
        self.site_name = site_name
        self.menu_parent_groups = menu_parent_groups
        self.permission = self._init_permission(self.permission)

    def _init_permission(self, permission):
        return self._generate_permission_set() if permission is None else deepcopy(permission)

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

        return urls

    def get_urls(self):
        return ()

    def get_menu_groups(self):
        menu_groups = list(self.menu_parent_groups)
        if self.menu_group:
            menu_groups += (self.menu_group,)
        return menu_groups

    def get_url_prefix(self):
        return '/'.join(self.get_menu_groups())

    def get_menu_group_pattern_name(self):
        return '-'.join(self.get_menu_groups())

    def get_verbose_name(self):
        return self.verbose_name

    def get_verbose_name_plural(self):
        return self.verbose_name_plural


class ModelCore(GetMethodFieldMixin, Core):

    abstract = True

    list_actions = ()

    register_model = True

    fields = ()
    list_fields = None

    default_ordering = None

    field_labels = {}

    can_read = True
    can_create = False
    can_update = False
    can_delete = False

    menu_group = None

    def get_fields(self, request, obj=None):
        return self.fields

    def get_field_labels(self, request):
        return self.field_labels

    def get_default_ordering(self):
        return self.default_ordering

    def get_queryset(self, request):
        raise NotImplementedError

    def get_list_actions(self, request, obj):
        return list(self.list_actions)

    def get_default_action(self, request, obj):
        return None


class DjangoCore(ModelCore):
    """
    Parent of REST and UI cores that works as controller to specific model.
    This class is abstract.
    """

    abstract = True

    # form params
    form_class = SmartModelForm
    form_edit_class = None
    form_add_class = None

    can_read = True
    can_create = True
    can_update = True
    can_delete = True

    def get_verbose_name(self):
        return self.model._meta.verbose_name if self.verbose_name is None else self.verbose_name

    def get_verbose_name_plural(self):
        return self.model._meta.verbose_name_plural if self.verbose_name_plural is None else self.verbose_name_plural

    def get_form_class(self, request, obj=None):
        return self.form_class

    def get_form_edit_class(self, request, obj=None):
        return self.form_edit_class or self.get_form_class(request, obj)

    def get_form_add_class(self, request, obj=None):
        return self.form_add_class or self.get_form_class(request, obj)

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
    def menu_group(self):
        return get_model_name(self.model)

    def get_default_ordering(self):
        return self.default_ordering if self.default_ordering is not None else (self.model._meta.ordering or ('pk',))

    def preload_queryset(self, request, qs):
        return qs

    def get_queryset(self, request):
        return self.model._default_manager.get_queryset().order_by(*self.get_default_ordering())


class UiCore(Core):
    """Main core for UI views."""

    abstract = True

    show_in_menu = True
    menu_url_name = None
    view_classes = ()
    default_ui_pattern_class = UiPattern

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
            return item_class(self.get_verbose_name_plural(), self.menu_url(request),
                              self.menu_group, self.is_active_menu_item(request, active_group))

    def menu_url(self, request):
        return self.ui_patterns.get(self.menu_url_name).get_url_string(request)


class RestCore(Core):
    """Main core for REST views."""

    rest_classes = ()
    default_rest_pattern_class = RestPattern
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
                    pattern, rest, RestPatternClass = rest_vals
                else:
                    pattern, rest = rest_vals
                    RestPatternClass = self.default_rest_pattern_class

                if isinstance(rest, str):
                    rest = getattr(self, rest)()

                pattern_names = [name]
                group_pattern_name = self.get_menu_group_pattern_name()
                if group_pattern_name:
                    pattern_names += [self.get_menu_group_pattern_name()]
                rest_patterns[name] = RestPatternClass('-'.join(pattern_names), self.site_name, pattern, rest, self)
        return rest_patterns

    def get_urls(self):
        return self.get_urlpatterns(self.rest_patterns)

    def get_api_url_name(self):
        return self.api_url_name or '{}:api-{}'.format(self.site_name, self.get_menu_group_pattern_name())

    def get_api_url(self, request):
        return reverse(self.get_api_url_name())

    def get_api_detail_url_name(self):
        return self.api_url_name or '{}:api-resource-{}'.format(self.site_name, self.get_menu_group_pattern_name())

    def get_api_detail_url(self, request, obj):
        return reverse(self.get_api_detail_url_name(), kwargs={'pk': obj.pk})


class UiRestCoreMixin:
    """Helper that joins urls generated wit REST core and UI core."""

    def get_urls(self):
        return self.get_urlpatterns(self.rest_patterns) + self.get_urlpatterns(self.ui_patterns)


class UiRestCore(UiRestCoreMixin, UiCore, RestCore):
    """UI REST Core, its main purpose is create custom REST resources and UI views."""

    abstract = True


class HomeUiCore(UiCore):

    menu_url_name = 'index'
    verbose_name_plural = _('Home')
    menu_group = 'home'
    abstract = settings.HOME_CORE != 'is_core.main.HomeUiCore'

    def get_view_classes(self):
        view_classes = super().get_view_classes()
        view_classes.append(('index', r'', import_string(settings.HOME_VIEW)))
        return view_classes

    def menu_url(self, request):
        return '/'

    def get_url_prefix(self):
        return ''


class ModelUiCore(ModelCore, UiCore):

    abstract = True

    menu_url_name = 'list'

    # list view params
    list_per_page = None
    default_list_filter = {}

    # add/edit view params
    fieldsets = None
    readonly_fields = None
    inline_views = None

    list_fields = None
    export_fields = None
    list_view_export_fields = None
    detail_view_export_fields = None
    export_types = settings.EXPORT_TYPES

    ui_add_view = None
    ui_detail_view = None
    ui_list_view = None

    @cached_property
    def default_model_view_classes(self):
        default_model_view_classes = []

        add_view = self.get_ui_add_view()
        detail_view = self.get_ui_detail_view()
        list_view = self.get_ui_list_view()

        if self.can_create and add_view:
            default_model_view_classes.append(('add', r'add/', add_view))
        if (self.can_read or self.can_update) and detail_view:
            default_model_view_classes.append(('detail', r'{}/'.format(PK_PATTERN), detail_view))
        if self.can_read and list_view:
            default_model_view_classes.append(('list', r'', list_view))
        return default_model_view_classes

    def get_view_classes(self):
        return super().get_view_classes() + list(self.default_model_view_classes)

    def get_ui_add_view(self):
        return self.ui_add_view

    def get_ui_detail_view(self):
        return self.ui_detail_view

    def get_ui_list_view(self):
        return self.ui_list_view

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets

    def get_fields(self, request, obj=None):
        fieldsets = self.get_fieldsets(request, obj)
        return flatten_fieldsets(fieldsets) if fieldsets is not None else self.fields

    def get_readonly_fields(self, request, obj=None):
        return [] if self.readonly_fields is None else self.readonly_fields

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return (
            self.menu_url_name in self.ui_patterns and self.show_in_menu and
            self.ui_patterns.get(self.menu_url_name).has_permission('get', request)
        )

    def get_inline_views(self, request, obj=None):
        return self.inline_views

    def get_default_list_filter(self, request):
        return self.default_list_filter.copy()

    def get_list_fields(self, request):
        return list(self.list_fields) if self.list_fields is not None else self.get_fields(request)

    def get_export_fields(self, request, obj=None):
        return list(self.export_fields) if self.export_fields is not None else self.get_list_fields(request)

    def get_export_types(self, request, obj=None):
        return list(self.export_types or ())

    def get_list_per_page(self, request):
        return self.list_per_page

    def get_add_url(self, request):
        return self.ui_patterns.get('add').get_url_string(request) if 'add' in self.ui_patterns else None

    @short_description(_('object name'))
    def _obj_name(self, obj):
        return str(obj)


class DjangoUiCore(DjangoCore, ModelUiCore):
    """Main core controller for specific model that provides UI views for model management (add, edit, list)."""

    abstract = True

    ui_add_view = DjangoAddFormView
    ui_detail_view = DjangoDetailFormView
    ui_list_view = DjangoTableView


class ModelRestCore(RestCore, ModelCore):
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
    rest_default_fields = ('_obj_name',)
    rest_filter_fields = None
    rest_filter_manager = None
    rest_extra_filter_fields = None
    rest_order_fields = None
    rest_extra_order_fields = None
    rest_register = True

    rest_form_edit_class = None
    rest_form_add_class = None

    rest_resource_class = None
    rest_field_labels = None
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

    def get_rest_field_labels(self, request):
        return (
            self.rest_field_labels if self.rest_field_labels is not None
            else self.get_field_labels(request)
        )

    def get_rest_form_add_class(self, request, obj=None):
        return self.rest_form_add_class or self.get_form_add_class(request, obj)

    def get_rest_form_edit_class(self, request, obj=None):
        return self.rest_form_edit_class or self.get_form_edit_class(request, obj)

    def get_rest_form_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def get_rest_form_exclude(self, request, obj=None):
        return []

    def get_rest_fields(self, request, obj=None):
        return self.rest_fields

    def get_rest_extra_fields(self, request, obj=None):
        return list(self.rest_extra_fields or ())

    def get_rest_detailed_fields(self, request, obj=None):
        return list(self.rest_detailed_fields or ())

    def get_rest_general_fields(self, request, obj=None):
        return list(self.rest_general_fields or ())

    def get_rest_guest_fields(self, request, obj=None):
        return list(self.rest_guest_fields or ())

    def get_rest_default_fields(self, request, obj=None):
        return list(self.rest_default_fields or ())

    def get_rest_filter_fields(self, request):
        return self.rest_filter_fields

    def get_rest_extra_filter_fields(self, request):
        return self.rest_extra_filter_fields

    def get_rest_order_fields(self, request):
        return list(self.rest_order_fields or ())

    def get_rest_extra_order_fields(self, request):
        return list(self.rest_extra_order_fields or ())

    def get_rest_class(self):
        resource_kwargs = {}
        resource_kwargs['paginator'] = self.rest_paginator
        if self.rest_filter_manager:
            resource_kwargs['filter_manager'] = self.rest_filter_manager
        return modelrest_factory(
            self.model, self.rest_resource_class,
            resource_kwargs=resource_kwargs,
            register=self.rest_register
        )

    def get_rest_patterns(self):
        rest_patterns = super().get_rest_patterns()
        rest_patterns.update(
            DoubleRestPattern(
                self.get_rest_class(), self.default_rest_pattern_class, self,
                self.get_rest_allowed_methods()
            ).patterns
        )
        return rest_patterns

    def get_list_actions(self, request, obj):
        list_actions = super().get_list_actions(request, obj)
        api_resource = self.rest_patterns.get('api-resource')
        if self.can_delete and api_resource.has_permission('delete', request, obj=obj):
            confirm_dialog = ConfirmRestAction.ConfirmDialog(_('Do you really want to delete "%s"') % obj)
            list_actions.append(ConfirmRestAction('api-resource-{}'.format(self.get_menu_group_pattern_name()),
                                                  _('Delete'), 'DELETE', confirm_dialog=confirm_dialog,
                                                  class_name='delete', success_text=_('Record "%s" was deleted') % obj))
        return list_actions

    # Resource extra fields

    def _rest_links(self, obj, request):
        rest_links = {}
        for pattern in self.rest_patterns.values():
            if pattern.send_in_rest:
                url = pattern.get_url_string(request, obj=obj)
                if url:
                    allowed_methods = pattern.get_allowed_methods(request, obj)
                    if allowed_methods:
                        rest_links[pattern.name] = {
                            'url': url,
                            'methods': [method.upper() for method in allowed_methods]
                        }
        return rest_links

    def _actions(self, obj, request):
        return self.get_list_actions(request, obj)

    def _default_action(self, obj, request):
        return self.get_default_action(request, obj=obj)


class DjangoRestCore(ModelRestCore, DjangoCore):
    """
    Main core controller for specific model that provides REST resources for model management.
    CRUD (POST, GET, PUT, DELETE).
    """

    abstract = True

    rest_resource_class = DjangoCoreResource
    rest_paginator = DjangoOffsetBasedPaginator()

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


class ModelUiRestCore(UiRestCoreMixin, ModelRestCore, ModelUiCore):

    abstract = True

    default_rest_extra_fields = (
        '_web_links', '_rest_links', '_default_action', '_actions', '_class_names', '_obj_name'
    )

    rest_obj_class_names = ()

    def get_rest_extra_fields(self, request, obj=None):
        return (
            super().get_rest_extra_fields(request, obj) +
            list(self.get_list_fields(request)) +
            list(self.get_export_fields(request)) +
            list(self.default_rest_extra_fields)
        )

    def get_list_actions(self, request, obj):
        list_actions = super().get_list_actions(request, obj)
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

    # Resource extra fields

    def _web_links(self, obj, request):
        web_links = {}
        for pattern in self.web_link_patterns(request):
            if pattern.send_in_rest:
                url = pattern.get_url_string(request, obj=obj)
                if url and pattern.has_permission('get', request, obj=obj):
                    web_links[pattern.name] = url
        return web_links

    def _class_names(self, obj, request):
        return self.get_rest_obj_class_names(request, obj)


class DjangoUiRestCore(DjangoRestCore, DjangoUiCore, ModelUiRestCore):
    """
    Combination of UI views and REST resources. UI views uses REST resources for printing model data, filtering,
    paging and so on.
    """

    abstract = True

    bulk_change_url_name = 'bulk-change'
    bulk_change_fields = ()

    bulk_change_enabled = False

    def get_rest_form_fields(self, request, obj=None):
        return list(set(super().get_rest_form_fields(request, obj)) | set(self.get_bulk_change_fields(request)))

    def get_rest_form_exclude(self, request, obj=None):
        return self.get_readonly_fields(request, obj)

    def get_view_classes(self):
        view_classes = super().get_view_classes()
        if self.is_bulk_change_enabled():
            view_classes.append((self.get_bulk_change_url_name(), r'bulk-change/?', BulkChangeFormView))
        return view_classes

    def is_bulk_change_enabled(self):
        return self.bulk_change_enabled

    def get_bulk_change_url_name(self):
        return self.bulk_change_url_name

    def get_bulk_change_fields(self, request):
        return self.bulk_change_fields
