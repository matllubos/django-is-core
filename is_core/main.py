from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import capfirst
from django.contrib.auth.decorators import login_required

from is_core.form import RestModelForm
from is_core.actions import WebAction, RestAction, WebActionPattern, RestActionPattern
from is_core.generic_views.form_views import AddModelFormView, EditModelFormView
from is_core.generic_views.table_views import TableView
from is_core.rest.handler import RestModelHandler
from is_core.rest.resource import RestModelResource
from is_core.auth.main import UIMiddleware


class ISCore(object):
    menu_group = None
    menu_subgroup = None
    menu_url_name = None
    menu_verbose_name = None
    show_in_menu = True

    def __init__(self, site_name):
        self.site_name = site_name
        self.views = self.get_views()

    def get_urlpatterns(self, views):
        urls = []
        for key, view_data in views.items():
            url_pattern, view = view_data[0:2]
            urls.append(url(url_pattern, view, name=key))
        urlpatterns = patterns('', *urls)
        return urlpatterns

    def get_urls(self):
        return self.get_urlpatterns(self.views)

    def get_show_in_menu(self, request):
        return self.show_in_menu

    def get_views(self):
        return {}

    def menu_url(self):
        return reverse(('%(site_name)s:' + self.menu_url_name) % {'site_name': self.site_name})


class ModelISCore(ISCore):
    exclude = []

    def save_model(self, request, obj, change):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()

    def menu_verbose_name(self):
        return self.model._meta.verbose_name_plural
    menu_verbose_name = property(menu_verbose_name)

    def menu_group(self):
        return str(self.model._meta.app_label)
    menu_group = property(menu_group)

    def menu_subgroup(self):
        return str(self.model._meta.module_name)
    menu_subgroup = property(menu_subgroup)

    def get_obj(self, pk):
        return get_object_or_404(self.model, pk=pk)


class UIModelISCore(UIMiddleware, ModelISCore):
    view_classes = {
                    'add': (r'^/add/$', AddModelFormView),
                    'edit': (r'^/(?P<pk>\d+)/$', EditModelFormView),
                    'list': (r'^/?$', TableView)
                    }

    show_in_menu = True
    api_url_name = None

    # list view params
    list_display = ()
    default_list_filter = {}
    list_actions = ()

    # add/edit view params
    fieldsets = ()
    fields = ()
    readonly_fields = ()
    inline_form_views = ()
    exclude = ()
    form_class = RestModelForm

    def get_show_in_menu(self, request):
        return 'list' in self.view_classes and self.show_in_menu;

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
        return self.readonly_fields

    def menu_url_name(self):
        info = self.menu_group, self.menu_subgroup
        return 'list-%s-%s' % info
    menu_url_name = property(menu_url_name)

    def bread_crumbs_url_names(self, context):
        view_type = context.get('view_type')

        bread_crumbs_url_names = [
                                    (_('List %s') % self.model._meta.verbose_name,
                                     'list' in self.view_classes and \
                                     '%s:list-%s-%s' % (self.site_name, self.menu_group, self.menu_subgroup) or None)
                                  ]
        if view_type == 'add':
            bread_crumbs_url_names.append((_('Add %s') % self.model._meta.verbose_name, None))
        elif view_type == 'edit':
            bread_crumbs_url_names.append((_('Edit %s') % self.model._meta.verbose_name, None))
        return bread_crumbs_url_names

    def get_view_classes(self):
        return self.view_classes.copy()

    def get_views(self):
        views = super(UIModelISCore, self).get_views()

        for name, view_vals in self.view_classes.items():
            pattern, view = view_vals

            views['%s-%s-%s' % (name, self.menu_group, self.menu_subgroup)] = \
                     (pattern, login_required(view.as_view(core=self),
                                              login_url='%s:login' % self.site_name))

        return views

    def default_list_actions(self, user):
        self._default_list_actions = []
        self._default_list_actions.append(WebAction('edit-%s-%s' % (self.menu_group, self.menu_subgroup),
                                                            _('Edit'), 'edit'))
        self._default_list_actions.append(RestAction('delete', _('Delete')))
        return self._default_list_actions

    def get_list_actions(self, user):
        list_actions = list(self.list_actions) + list(self.default_list_actions(user))
        return list_actions

    def gel_api_url_name(self):
        return self.api_url_name


class RestModelISCore(ModelISCore):
    show_in_menu = False

    rest_list_fields = ()
    rest_obj_fields = ()
    form_class = RestModelForm
    rest_allowed_methods = ('GET', 'DELETE', 'POST', 'PUT')
    rest_handler = RestModelHandler

    def __init__(self, site_name):
        super(RestModelISCore, self).__init__(site_name)
        self.rest_resources = self.get_rest_resources()

    def get_rest_list_fields(self):
        return list(self.rest_list_fields)

    def get_rest_obj_fields(self):
        return list(self.rest_obj_fields)

    def get_rest_resources(self):
        info = self.menu_group, self.menu_subgroup
        rest_resource = RestModelResource(name='Api%s%sHandler' % tuple([capfirst(name) for name in info]), core=self)
        rest_resources = {
                           'api-resource-%s-%s' % (self.menu_group, self.menu_subgroup):
                                (r'^/api/(?P<pk>\d+)/?$', rest_resource, ('GET', 'PUT', 'DELETE')),
                           'api-%s-%s' % (self.menu_group, self.menu_subgroup):
                                (r'^/api/?$', rest_resource, ('GET', 'POST'))
                           }
        return rest_resources

    def get_urls(self):
        urls = self.get_urlpatterns(self.rest_resources)
        return urls + super(RestModelISCore, self).get_urls()

    def get_list_actions_patterns(self, obj=None):
        list_actions_patterns = []
        for key in self.views.keys():
            list_actions_patterns.append(WebActionPattern(key, self.site_name))
        return list_actions_patterns

    def get_list_resources_patterns(self, user, obj=None):
        list_resources_patterns = []
        for key, resource in self.rest_resources.items():
            methods = resource[1].handler.get_allowed_methods(user, obj.pk)
            if len(resource) > 2:
                methods = set(methods) & set(resource[2])
            list_resources_patterns.append(RestActionPattern(key, self.site_name, methods))
        return list_resources_patterns


class UIRestModelISCore(UIModelISCore, RestModelISCore):

    def get_rest_list_fields(self):
        return list(self.rest_list_fields) or list(self.list_display)

    def gel_api_url_name(self):
        info = self.site_name, self.menu_group, self.menu_subgroup
        return self.api_url_name or '%s:api-%s-%s' % info
