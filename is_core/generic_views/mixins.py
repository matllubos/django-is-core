from __future__ import unicode_literals

from django.core.urlresolvers import reverse


class ListParentMixin(object):

    add_current_to_breadcrumbs = True

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import MenuItem

        menu_items = super(ListParentMixin, self).bread_crumbs_menu_items()
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(self.model._ui_meta.list_verbose_name %
                                       {'verbose_name': self.model._meta.verbose_name,
                                        'verbose_name_plural': self.model._meta.verbose_name_plural},
                                       reverse('%s:list-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name())),
                                       not self.add_current_to_breadcrumbs))
        if self.add_current_to_breadcrumbs:
            menu_items.append(MenuItem(self.get_title(), self.request.path, True))
        return menu_items


class EditParentMixin(object):

    add_current_to_breadcrumbs = True

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import MenuItem

        menu_items = super(EditParentMixin, self).bread_crumbs_menu_items()
        if 'list' in self.core.ui_patterns \
            and self.core.ui_patterns.get('list').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(self.model._ui_meta.list_verbose_name %
                                       {'verbose_name': self.model._meta.verbose_name,
                                        'verbose_name_plural': self.model._meta.verbose_name_plural},
                                       reverse('%s:list-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name())),
                                       False))
        if 'edit' in self.core.ui_patterns \
            and self.core.ui_patterns.get('edit').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(self.model._ui_meta.edit_verbose_name %
                                       {'verbose_name': self.model._meta.verbose_name,
                                        'verbose_name_plural': self.model._meta.verbose_name_plural,
                                        'obj': self.get_obj(True)},
                                       reverse('%s:edit-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name()),
                                                args=(self.request.kwargs.get('pk'),)),
                                       not self.add_current_to_breadcrumbs))
        if self.add_current_to_breadcrumbs:
            menu_items.append(MenuItem(self.get_title(), self.request.path, True))
        return menu_items
