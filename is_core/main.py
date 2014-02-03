from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from is_core.form import RestModelForm
from is_core.actions import WebAction, RestAction
from is_core.generic_views.form_views import AddModelFormView, EditModelFormView
from is_core.generic_views.table_views import TableView


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
            pattern_name = '%s-%s-%s' % (key, self.menu_group, self.menu_subgroup)
            urls.append(url(url_pattern, view, name=pattern_name))
        urlpatterns = patterns('', *urls)
        return urlpatterns

    def get_urls(self):
        return self.get_urlpatterns(self.views)

    def get_show_in_menu(self, request):
        return self.show_in_menu

    def get_views(self):
        return {}

    def menu_url(self, account, environment):
        return reverse(('%(site_name)s:' + self.menu_url_name) % {'site_name': self.site_name},
                args=(account, environment))


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


class UIISCore(ModelISCore):
    list_display = ()
    inline_form_views = ()
    add_view = AddModelFormView
    edit_view = EditModelFormView
    table_view = TableView
    show_in_menu = True
    fieldsets = ()
    default_list_filter = {}
    api_url_name = None
    list_actions = ()
    form_class = RestModelForm

    def get_show_in_menu(self, request):
        return 'list' in self.allowed_views and self.show_in_menu;

    def get_rest_list_fields(self):
        return list(self.list_display)

    def get_inline_form_views(self, request, obj=None):
        return self.inline_form_views

    def get_default_list_filter(self, request):
        return self.default_list_filter.copy()

    def menu_url_name(self):
        info = self.menu_group, self.menu_subgroup
        return 'list-%s-%s' % info
    menu_url_name = property(menu_url_name)

    def get_fieldsets(self, form):
        return list(self.fieldsets)

    def bread_crumbs_url_names(self, context):
        request = context.get('request')
        view_type = context.get('view_type')

        bread_crumbs_url_names = [
                                    (_('List %s') % self.model._meta.verbose_name,
                                     'list' in self.allowed_views and \
                                     self.has_read_permission(request.user, request.account_pk) and \
                                     '%s:list-%s-%s' % (self.site_name, self.menu_group, self.menu_subgroup) or None)
                                  ]
        if view_type == 'add':
            bread_crumbs_url_names.append((_('Add %s') % self.model._meta.verbose_name, None))
        elif view_type == 'edit':
            bread_crumbs_url_names.append((_('Edit %s') % self.model._meta.verbose_name, None))
        return bread_crumbs_url_names

    def get_views(self):
        views = super(UIISCore, self).get_views()

        if 'list' in self.allowed_views:
            views['list-%s-%s' % (self.menu_group, self.menu_subgroup)] = \
                        (r'^/?$', self.table_view.as_view(persoo_view=self))

        if 'add' in self.allowed_views:
            views['add-%s-%s' % (self.menu_group, self.menu_subgroup)] = \
                        (r'^/add/$', self.add_view.as_view(persoo_view=self))

        if 'edit' in self.allowed_views:
            views['edit-%s-%s' % (self.menu_group, self.menu_subgroup)] = \
                        (r'^/(?P<pk>\d+)/$', self.edit_view.as_view(persoo_view=self))
        return views

    def default_list_actions(self, user, account_pk):
        self._default_list_actions = []
        self._default_list_actions.append(WebAction('edit-%s-%s' % (self.menu_group, self.menu_subgroup),
                                                            _('Edit'), 'edit'))
        self._default_list_actions.append(RestAction('delete', _('Delete')))
        return self._default_list_actions

    def get_list_actions(self, user, account_pk):
        list_actions = list(self.list_actions) + list(self.default_list_actions(user, account_pk))
        return list_actions

    def gel_api_url_name(self):
        return self.api_url_name
