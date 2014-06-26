from __future__ import unicode_literals

import sys

from django.conf.urls import patterns as django_patterns
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.http.response import Http404
from django.core.exceptions import ValidationError
from django.utils import six

from piston.utils import list_to_dict, dict_to_list, join_dicts

from is_core.forms import RestModelForm
from is_core.actions import WebAction, ConfirmRestAction
from is_core.generic_views.form_views import AddModelFormView, EditModelFormView
from is_core.generic_views.table_views import TableView
from is_core.rest.resource import RestModelResource
from is_core.auth.main import PermissionsMixin, PermissionsUIMixin, PermissionsRestMixin
from is_core.patterns import UIPattern, RestPattern
from is_core.utils import flatten_fieldsets, str_to_class, get_new_class_name
from is_core import config
from is_core.menu import LinkMenuItem
from is_core.loading import register_core


class ISCoreBase(type):
    def __new__(cls, *args, **kwargs):
        name, _, attrs = args

        abstract = attrs.pop('abstract', False)

        super_new = super(ISCoreBase, cls).__new__
        new_class = super_new(cls, *args, **kwargs)
        model_module = sys.modules[new_class.__module__]
        app_label = model_module.__name__.split('.')[-2]

        if name != 'NewBase' and not abstract:
            register_core(app_label, new_class)
        return new_class


class ISCore(six.with_metaclass(ISCoreBase)):
    abstract = True

    menu_url_name = None
    verbose_name = None
    verbose_name_plural = None
    menu_group = None

    def __init__(self, site_name, menu_parent_groups):
        self.site_name = site_name
        self.menu_parent_groups = menu_parent_groups

    def init_request(self, request):
        pass

    def init_ui_request(self, request):
        self.init_request(request)

    def init_rest_request(self, request):
        self.init_request(request)

    def get_urlpatterns(self, patterns):
        urls = []
        for pattern in patterns.values():
            pattern.url_prefix = self.get_url_prefix()
            url = pattern.get_url()
            if url:
                urls.append(url)
        urlpatterns = django_patterns('', *urls)
        return urlpatterns

    def get_urls(self):
        return ()

    def get_show_in_menu(self, request):
        return self.show_in_menu

    def get_views(self):
        return {}

    def menu_url(self, request):
        return reverse(('%(site_name)s:' + self.menu_url_name) % {'site_name': self.site_name})

    def get_menu_groups(self):
        menu_groups = list(self.menu_parent_groups)
        if self.menu_group:
            menu_groups += (self.menu_group,)
        return menu_groups

    def get_url_prefix(self):
        return '/'.join(self.get_menu_groups())

    def get_menu_group_pattern_name(self):
        return '-'.join(self.get_menu_groups())

    def get_menu_item(self, request, active_group):
        pass


class ModelISCore(PermissionsMixin, ISCore):
    abstract = True

    list_actions = ()

    # form params
    form_fields = None
    form_inline_views = ()
    form_exclude = ()
    form_class = RestModelForm

    ordering = None

    def get_form_fields(self, request, obj=None):
        return self.form_fields

    def get_form_class(self, request, obj=None):
        return self.form_class

    def get_form_exclude(self, request, obj=None):
        return self.form_exclude

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

    def verbose_name(self):
        return self.model._meta.verbose_name
    verbose_name = property(verbose_name)

    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural
    verbose_name_plural = property(verbose_name_plural)

    def menu_group(self):
        return str(self.model._meta.module_name)
    menu_group = property(menu_group)

    def get_obj(self, request, **filters):
        try:
            return get_object_or_404(self.get_queryset(request), **filters)
        except (ValidationError, ValueError):
            raise Http404

    def get_ordering(self):
        return self.model._meta.ordering or ('pk',)

    def get_queryset(self, request):
        return self.model._default_manager.get_queryset().order_by(*self.get_ordering())

    def get_list_actions(self, request, obj):
        return list(self.list_actions)


class UIISCore(PermissionsUIMixin, ISCore):
    abstract = True

    api_url_name = None
    show_in_menu = True
    menu_url_name = None
    _ui_patterns = None
    view_classes = SortedDict()
    default_ui_pattern_class = UIPattern

    def get_view_classes(self):
        return self.view_classes.copy()

    @property
    def ui_patterns(self):
        if not self._ui_patterns:
            self._ui_patterns = self.get_ui_patterns()
        return self._ui_patterns

    def get_ui_patterns(self):
        ui_patterns = SortedDict()
        for name, view_vals in self.get_view_classes().items():
            if len(view_vals) == 3:
                pattern, view, ViewPatternClass = view_vals
            else:
                pattern, view = view_vals
                ViewPatternClass = self.default_ui_pattern_class

            pattern_names = [name]
            group_pattern_name = self.get_menu_group_pattern_name()
            if group_pattern_name:
                pattern_names += [self.get_menu_group_pattern_name()]

            ui_patterns[name] = ViewPatternClass('-'.join(pattern_names), self.site_name, pattern, view, self)
        return ui_patterns

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return self.has_ui_read_permission(request)

    def get_menu_item(self, request, active_group):
        if self.get_show_in_menu(request):
            return LinkMenuItem(self.verbose_name_plural, self.menu_url(request),
                                self.menu_group, active_group == self.menu_group)



class HomeUIISCore(UIISCore):

    menu_url_name = 'index'
    verbose_name_plural = _('Home')
    menu_group = 'home'
    abstract = config.HOME_VIEW != 'is_core.generic_views.HomeView'

    def get_view_classes(self):
        HomeView = str_to_class(config.HOME_VIEW)
        return SortedDict((
                        ('index', (r'^$', HomeView)),
                    ))

    def menu_url(self, request):
        return '/'

    def get_url_prefix(self):
        return ''


class UIModelISCore(ModelISCore, UIISCore):
    abstract = True

    view_classes = SortedDict((
                        ('add', (r'^/add/$', AddModelFormView)),
                        ('edit', (r'^/(?P<pk>[-\w]+)/$', EditModelFormView)),
                        ('list', (r'^/?$', TableView)),
                    ))

    # list view params
    list_display = ('_obj_name',)
    default_list_filter = {}

    # add/edit view params
    form_fieldsets = None
    form_readonly_fields = ()

    def __init__(self, site_name, menu_parent_groups):
        super(UIModelISCore, self).__init__(site_name, menu_parent_groups)

    def get_form_fieldsets(self, request, obj=None):
        return self.form_fieldsets

    def get_form_readonly_fields(self, request, obj=None):
        return self.form_readonly_fields

    def get_ui_form_fields(self, request, obj=None):
        return self.get_form_fields(request, obj)

    def get_ui_form_class(self, request, obj=None):
        return self.get_form_class(request, obj)

    def get_ui_form_exclude(self, request, obj=None):
        return self.get_form_exclude(request, obj)

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return 'list' in self.view_classes and self.show_in_menu and self.has_ui_read_permission(request)

    def get_rest_list_fields(self):
        return self.list_display

    def get_form_inline_views(self, request, obj=None):
        return self.form_inline_views

    def get_default_list_filter(self, request):
        return self.default_list_filter.copy()

    @property
    def menu_url_name(self):
        return 'list-%s' % self.get_menu_group_pattern_name()

    def get_list_display(self):
        return self.list_display

    def get_ui_list_display(self, request):
        return list(self.get_list_display())

    def get_list_actions(self, request, obj):
        list_actions = super(UIModelISCore, self).get_list_actions(request, obj)
        list_actions.append(WebAction('edit-%s' % self.get_menu_group_pattern_name(), _('Edit'), 'edit'))
        return list_actions

    def get_api_url_name(self):
        return self.api_url_name

    def get_add_url(self, request):
        return self.ui_patterns.get('add').get_url_string(request)

    def get_api_url(self, request):
        return reverse(self.get_api_url_name())


class RestModelISCore(PermissionsRestMixin, ModelISCore):
    abstract = True

    # Allowed rest fields
    rest_fields = None
    # Default rest fields for list
    rest_default_list_fields = None
    # Default rest fields for one object
    rest_default_obj_fields = None

    form_class = RestModelForm
    rest_allowed_methods = ('GET', 'DELETE', 'POST', 'PUT')
    rest_obj_class_names = ()

    rest_resource_class = RestModelResource
    _resource_patterns = None

    def __init__(self, site_name, menu_parent_groups):
        super(RestModelISCore, self).__init__(site_name, menu_parent_groups)

    def get_rest_form_fields(self, request, obj=None):
        return self.get_form_fields(request, obj)

    def get_rest_form_class(self, request, obj=None):
        return self.get_form_class(request, obj)

    def get_rest_form_exclude(self, request, obj=None):
        return self.get_form_exclude(request, obj)

    def get_rest_fields(self):
        if self.rest_fields:
            return self.rest_fields

        rest_fields = list_to_dict(self.model._rest_meta.fields)

        rest_default_list_fields = list_to_dict(self.get_rest_default_list_fields())
        rest_default_obj_fields = list_to_dict(self.get_rest_default_obj_fields())

        return dict_to_list(join_dicts(join_dicts(rest_fields, rest_default_list_fields), rest_default_obj_fields))

    def get_rest_default_list_fields(self):
        return self.rest_default_list_fields or self.model._rest_meta.default_list_fields

    def get_rest_default_obj_fields(self):
        return self.rest_default_obj_fields or self.model._rest_meta.default_obj_fields

    def get_rest_obj_class_names(self, request, obj):
        return list(self.rest_obj_class_names)

    def get_urls(self):
        return self.get_urlpatterns(self.resource_patterns)

    @property
    def resource_patterns(self):
        if not self._resource_patterns:
            self._resource_patterns = self.get_resource_patterns()
        return self._resource_patterns

    _rest_resource = None
    @property
    def rest_resource(self):
        if not self._rest_resource:
            resource_kwargs = {
                      'model': self.model, 'fields': set(self.rest_resource_class.fields + self.get_rest_fields()),
                      'default_list_fields': self.get_rest_default_list_fields(),
                      'default_obj_fields': self.get_rest_default_list_fields(), 'form_class': self.form_class,
                      'site_name': self.site_name, 'menu_group': self.menu_group, 'core': self, 'register': True
                      }
            self._rest_resource = type(str(get_new_class_name('api-resource-%s' % self.get_menu_group_pattern_name(),
                                                              self.rest_resource_class)),
                                       (self.rest_resource_class,), resource_kwargs)
        return self._rest_resource

    def get_resource_patterns(self):
        resource_patterns = SortedDict()
        resource_patterns['api-resource'] = RestPattern('api-resource-%s' % self.get_menu_group_pattern_name(),
                                                        self.site_name, r'^/api/(?P<pk>[-\w]+)/?$', self.rest_resource,
                                                        self, ('GET', 'PUT', 'DELETE'))
        resource_patterns['api'] = RestPattern('api-%s' % self.get_menu_group_pattern_name(),
                                                self.site_name, r'^/api/?$', self.rest_resource, self, ('GET', 'POST'))
        return resource_patterns

    def get_list_actions(self, request, obj):
        list_actions = super(RestModelISCore, self).get_list_actions(request, obj)
        if self.has_delete_permission(request, obj):
            confirm_dialog = ConfirmRestAction.ConfirmDialog(_('Do you really want to delete "%s"') %
                                                             obj)
            list_actions.append(ConfirmRestAction('api-resource-%s' % self.get_menu_group_pattern_name(),
                                                  _('Delete') , 'DELETE', confirm_dialog=confirm_dialog,
                                                  class_name='delete'))
        return list_actions

    def web_link_patterns(self, request):
        return self.ui_patterns.values()


class UIRestModelISCore(RestModelISCore, UIModelISCore):
    abstract = True

    def get_urls(self):
        return self.get_urlpatterns(self.resource_patterns) + self.get_urlpatterns(self.ui_patterns)

    def get_rest_default_list_fields(self):
        rest_list_fields_dict = list_to_dict(super(UIRestModelISCore, self).get_rest_default_list_fields())

        for display in self.get_list_display():
            rest_dict = rest_list_fields_dict
            for val in display.split('__'):
                rest_dict[val] = rest_dict.get(val, {})
                rest_dict = rest_dict[val]

        return dict_to_list(rest_list_fields_dict)

    def get_api_url_name(self):
        return self.api_url_name or '%s:api-%s' % (self.site_name, self.get_menu_group_pattern_name())

    def get_rest_form_fields(self, request, obj=None):
        return flatten_fieldsets(self.get_form_fieldsets(request, obj)) or self.get_form_fields(request, obj)

    def get_rest_form_exclude(self, request, obj=None):
        return self.get_form_readonly_fields(request, obj) + self.get_form_exclude(request, obj)
