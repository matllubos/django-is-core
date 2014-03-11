from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


class ListParentMixin(object):

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import MenuItem

        menu_items = super(ListParentMixin, self).bread_crumbs_menu_items()
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(_('List %s') % self.core.verbose_name_plural,
                                       reverse('%s:list-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name())),
                                       False))
        menu_items.append(MenuItem(self.get_title(), self.request.path, True))
        return menu_items


class EditParentMixin(object):

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import MenuItem

        menu_items = super(EditParentMixin, self).bread_crumbs_menu_items()
        if 'list' in self.core.ui_patterns \
            and self.core.ui_patterns.get('list').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(_('List %s') % self.core.verbose_name_plural,
                                       reverse('%s:list-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name())),
                                       False))
        if 'edit' in self.core.ui_patterns \
            and self.core.ui_patterns.get('edit').view.has_get_permission(self.request, self.core):
            menu_items.append(MenuItem(_('Edit %s') % self.core.verbose_name,
                                       reverse('%s:edit-%s' % (self.site_name,
                                                               self.core.get_menu_group_pattern_name()),
                                                args=(self.request.kwargs.get('pk'))),
                                       False))
        menu_items.append(MenuItem(self.get_title(), self.request.path, True))
        return menu_items
