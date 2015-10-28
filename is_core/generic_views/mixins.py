from __future__ import unicode_literals

from .exceptions import GenericViewException


class ListParentMixin(object):

    def list_bread_crumbs_menu_item(self):
        from is_core.menu import LinkMenuItem

        list_pattern = self.core.ui_patterns.get('list')
        list_view = list_pattern.get_view(self.request)
        return LinkMenuItem(self.model._ui_meta.list_verbose_name %
                            {'verbose_name': list_view.model._meta.verbose_name,
                             'verbose_name_plural': list_view.model._meta.verbose_name_plural},
                             list_pattern.get_url_string(self.request),
                             active=not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = []
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').get_view(self.request).has_get_permission():
            menu_items.append(self.list_bread_crumbs_menu_item())
        return menu_items

    def extra_bread_crumbs_menu_items(self):
        return self.parent_bread_crumbs_menu_items()


class EditParentMixin(ListParentMixin):

    def edit_bread_crumbs_menu_item(self):
        from is_core.menu import LinkMenuItem

        edit_pattern = self.core.ui_patterns.get('edit')
        edit_view = edit_pattern.get_view(self.request)
        parent_obj = self.get_parent_obj()
        if not isinstance(parent_obj, edit_view.model):
            raise GenericViewException('Parent obj must be instance of edit view model')

        return LinkMenuItem(self.model._ui_meta.edit_verbose_name %
                            {'verbose_name': edit_view.model._meta.verbose_name,
                             'verbose_name_plural': edit_view.model._meta.verbose_name_plural,
                             'obj': parent_obj},
                             edit_pattern.get_url_string(self.request, kwargs={'pk':parent_obj.pk}),
                             active=not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = super(EditParentMixin, self).parent_bread_crumbs_menu_items()
        if 'edit' in self.core.ui_patterns \
                and self.core.ui_patterns.get('edit').get_view(self.request).has_get_permission(obj=self.get_obj()):
            menu_items.append(self.edit_bread_crumbs_menu_item())
        return menu_items

    def get_parent_obj(self):
        return self.get_obj()


class TabsViewMixin(object):

    tabs = ()

    def get_tabs(self):
        return self.tabs

    def get_tab_menu_items(self):
        from is_core.menu import LinkMenuItem

        menu_items = []
        for tab in self.get_tabs():
            if len(tab) == 2:
                tab_title, tab_url = tab
                is_active = self.request.path == tab_url
            else:
                tab_title, tab_url, is_active = tab

            menu_items.append(LinkMenuItem(tab_title, tab_url, active=is_active))
        return menu_items

    def get_context_data(self, form=None, **kwargs):
        context_data = super(TabsViewMixin, self).get_context_data(form=form, **kwargs)
        context_data.update({
            'tabs': self.get_tab_menu_items(),
        })
        return context_data


class GetCoreObjViewMixin(object):
    pk_name = 'pk'

    def get_obj_filters(self):
        filters = {'pk': self.kwargs.get(self.pk_name)}
        return filters

    # TODO: should contains own implementation (not use get_obj from main)
    _obj = None
    def get_obj(self, cached=True):
        if cached and self._obj:
            return self._obj
        obj = self.core.get_obj(self.request, **self.get_obj_filters())
        if cached and not self._obj:
            self._obj = obj
        return obj
