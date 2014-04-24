from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404


class ListParentMixin(object):

    add_current_to_breadcrumbs = True

    def list_bread_crumbs_menu_item(self):
        from is_core.templatetags.menu import LinkMenuItem

        return LinkMenuItem(self.model._ui_meta.list_verbose_name %
                            {'verbose_name': self.model._meta.verbose_name,
                             'verbose_name_plural': self.model._meta.verbose_name_plural},
                            reverse('%s:list-%s' % (self.site_name, self.core.get_menu_group_pattern_name())),
                                           not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = []
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request):
            menu_items.append(self.list_bread_crumbs_menu_item())
        return menu_items

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import LinkMenuItem

        menu_items = super(ListParentMixin, self).bread_crumbs_menu_items()
        menu_items += self.parent_bread_crumbs_menu_items()
        if self.add_current_to_breadcrumbs:
            menu_items.append(LinkMenuItem(self.get_title(), self.request.path, True))
        return menu_items


class EditParentMixin(ListParentMixin):

    def edit_bread_crumbs_menu_item(self):
        from is_core.templatetags.menu import LinkMenuItem

        return LinkMenuItem(self.model._ui_meta.edit_verbose_name %
                            {'verbose_name': self.model._meta.verbose_name,
                             'verbose_name_plural': self.model._meta.verbose_name_plural,
                             'obj': self.get_obj(True)},
                             reverse('%s:edit-%s' % (self.site_name, self.core.get_menu_group_pattern_name()),
                                                    args=(self.request.kwargs.get('pk'),)),
                                                    not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = super(EditParentMixin, self).parent_bread_crumbs_menu_items()
        if 'edit' in self.core.ui_patterns \
                and self.core.ui_patterns.get('edit').view.has_get_permission(self.request):
            menu_items.append(self.edit_bread_crumbs_menu_item())
        return menu_items


class TabsViewMixin(object):

    tabs = ()

    def get_tabs(self):
        return self.tabs

    def get_tab_menu_items(self):
        from is_core.templatetags.menu import LinkMenuItem

        menu_items = []
        for tab in self.get_tabs():
            if len(tab) == 2:
                tab_title, tab_url = tab
                is_active = self.request.path == tab_url
            else:
                tab_title, tab_url, is_active = tab

            menu_items.append(LinkMenuItem(tab_title, tab_url, is_active))
        return menu_items

    def get_context_data(self, form=None, **kwargs):
        context_data = super(TabsViewMixin, self).get_context_data(form=form, **kwargs)
        context_data.update({
            'tabs': self.get_tab_menu_items(),
        })
        return context_data


class GetCoreObjViewMixin(object):

    def get_obj_filters(self):
        filters = {'pk': self.kwargs.get('pk')}
        return filters

    _obj = None
    def get_obj(self, cached=True):
        if cached and self._obj:
            return self._obj
        obj = self.core.get_obj(self.request, **self.get_obj_filters())
        if cached and not self._obj:
            self._obj = obj
        return obj
