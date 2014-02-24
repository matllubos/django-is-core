from django.conf.urls import patterns as django_patterns
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from is_core.form import RestModelForm
from is_core.actions import WebAction, RestAction
from is_core.generic_views.form_views import AddModelFormView, EditModelFormView
from is_core.generic_views.table_views import TableView
from is_core.rest.handler import RestModelHandler
from is_core.rest.resource import RestModelResource
from is_core.auth.main import PermissionsMixin, PermissionsUIMixin, PermissionsRestMixin
from is_core.utils import list_to_dict, dict_to_list
from is_core.patterns import UIPattern, RestPattern


class ISCore(object):
    menu_subgroup = None
    menu_url_name = None
    verbose_name = None
    verbose_name_plural = None
    show_in_menu = True

    def __init__(self, site_name, menu_parent_groups):
        self.site_name = site_name
        self.menu_parent_groups = menu_parent_groups

    def get_urlpatterns(self, patterns):
        urls = []
        for pattern in patterns:
            urls.append(pattern.get_url())
        urlpatterns = django_patterns('', *urls)
        return urlpatterns

    def get_urls(self):
        return ()

    def get_show_in_menu(self, request):
        return self.show_in_menu

    def get_views(self):
        return {}

    def menu_url(self):
        return reverse(('%(site_name)s:' + self.menu_url_name) % {'site_name': self.site_name})

    def get_menu_groups(self):
        return self.menu_parent_groups + (self.menu_group,)

    def get_menu_group_pattern_name(self):
        return '-'.join(self.get_menu_groups())


class ModelISCore(PermissionsMixin, ISCore):
    exclude = []
    list_actions = ()

    def pre_save_model(self, request, obj, change):
        pass

    def save_model(self, request, obj, change):
        obj.save()

    def post_save_model(self, request, obj, change):
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

    def get_obj(self, pk):
        return get_object_or_404(self.model, pk=pk)

    def get_queryset(self, request):
        return self.model._default_manager.get_queryset()

    def get_list_actions(self, request, obj):
        return list(self.list_actions)


class UIModelISCore(PermissionsUIMixin, ModelISCore):
    view_classes = {
                    'add': (r'^/add/$', AddModelFormView),
                    'edit': (r'^/(?P<pk>[-\w]+)/$', EditModelFormView),
                    'list': (r'^/?$', TableView)
                    }

    show_in_menu = True
    api_url_name = None

    # list view params
    list_display = ()
    default_list_filter = {}

    # add/edit view params
    fieldsets = ()
    fields = ()
    readonly_fields = ()
    inline_form_views = ()
    exclude = ()
    form_class = RestModelForm

    def __init__(self, site_name, menu_parent_groups):
        super(UIModelISCore, self).__init__(site_name, menu_parent_groups)
        self.ui_patterns = self.get_view_patterns()

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns)

    def get_show_in_menu(self, request):
        return 'list' in self.view_classes and self.show_in_menu and self.has_read_permission(request)

    def get_rest_list_fields(self):
        return self.list_display

    def get_inline_form_views(self, request, obj=None):
        return self.inline_form_views

    def get_default_list_filter(self, request):
        return self.default_list_filter.copy()

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets

    def get_fields(self, request, obj=None):
        return self.fields

    def get_form_class(self, request, obj=None):
        return self.form_class

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def get_exclude(self, request, obj=None):
        return self.exclude

    def menu_url_name(self):
        return 'list-%s' % self.get_menu_group_pattern_name()
    menu_url_name = property(menu_url_name)

    def bread_crumbs_url_names(self, context):
        view_type = context.get('view_type')

        bread_crumbs_url_names = []

        if 'list' in self.view_classes:
            bread_crumbs_url_names.append(
                                    (_('List %s') % self.verbose_name_plural,
                                     '%s:list-%s' % (self.site_name, self.get_menu_group_pattern_name()))
                                  )

        if view_type == 'add':
            bread_crumbs_url_names.append((_('Add %s') % self.verbose_name, None))
        elif view_type == 'edit':
            bread_crumbs_url_names.append((_('Edit %s') % self.verbose_name, None))
        return bread_crumbs_url_names

    def get_view_classes(self):
        return self.view_classes.copy()

    def get_view_patterns(self):
        view_patterns = []
        for name, view_vals in self.get_view_classes().items():
            if len(view_vals) == 3:
                pattern, view, ViewPatternClass = view_vals
            else:
                pattern, view = view_vals
                ViewPatternClass = UIPattern

            if view.login_required:
                view_instance = view.as_wrapped_view(core=self)
            else:
                view_instance = view.as_view(core=self)
            view_patterns.append(ViewPatternClass('%s-%s' % (name, self.get_menu_group_pattern_name()),
                                                  self.site_name, pattern, view_instance))
        return view_patterns

    def get_list_display(self):
        return self.list_display

    def get_list_actions(self, request, obj):
        list_actions = super(UIModelISCore, self).get_list_actions(request, obj)
        list_actions.append(WebAction('edit-%s' % self.get_menu_group_pattern_name(), _('Edit'), 'edit'))
        return list_actions

    def gel_api_url_name(self):
        return self.api_url_name


class RestModelISCore(PermissionsRestMixin, ModelISCore):
    show_in_menu = False

    rest_list_fields = ()
    rest_obj_fields = ()
    form_class = RestModelForm
    rest_allowed_methods = ('GET', 'DELETE', 'POST', 'PUT')
    rest_handler = RestModelHandler
    rest_obj_class_names = ()

    def __init__(self, site_name, menu_parent_groups):
        super(RestModelISCore, self).__init__(site_name, menu_parent_groups)
        self.resource_patterns = self.get_resource_patterns()

    def get_rest_list_fields(self):
        return list(self.rest_list_fields)

    def get_rest_obj_fields(self):
        return list(self.rest_obj_fields)

    def get_rest_obj_class_names(self, request, obj):
        return list(self.rest_obj_class_names)

    def get_urls(self):
        return self.get_urlpatterns(self.resource_patterns)

    def get_resource_patterns(self):
        resource = RestModelResource(name='Api%sHandler' % self.get_menu_group_pattern_name(), core=self)
        resource_patterns = (
                                RestPattern('api-resource-%s' % self.get_menu_group_pattern_name(),
                                            self.site_name, r'^/api/(?P<pk>[-\w]+)/?$', resource, ('GET', 'PUT', 'DELETE')),
                                RestPattern('api-%s' % self.get_menu_group_pattern_name(),
                                            self.site_name, r'^/api/?$', resource, ('GET', 'POST')),
                           )
        return resource_patterns

    def get_list_actions(self, request, obj):
        list_actions = super(RestModelISCore, self).get_list_actions(request, obj)
        if self.has_delete_permission(request, obj):
            list_actions.append(RestAction('api-resource-%s' % self.get_menu_group_pattern_name(),
                                                         _('Delete') , 'DELETE'))
        return list_actions


class UIRestModelISCore(UIModelISCore, RestModelISCore):

    def get_urls(self):
        return self.get_urlpatterns(self.ui_patterns) + self.get_urlpatterns(self.resource_patterns)

    def get_rest_list_fields(self):
        rest_list_fields_dict = list_to_dict(self.rest_list_fields)

        for display in self.get_list_display():
            rest_dict = rest_list_fields_dict
            for val in display.split('__'):
                rest_dict[val] = rest_dict.get(val, {})
                rest_dict = rest_dict[val]

        return dict_to_list(rest_list_fields_dict)

    def gel_api_url_name(self):
        return self.api_url_name or '%s:api-%s' % (self.site_name, self.get_menu_group_pattern_name())
