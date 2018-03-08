from copy import deepcopy

from django.utils.encoding import python_2_unicode_compatible


class MenuItem:

    def __init__(self, title, collapsible, group, active=False, submenu_items=[]):
        self.title = title
        self.collapsible = collapsible
        self.submenu_items = submenu_items
        self.group = group
        self.active = active


@python_2_unicode_compatible
class LinkMenuItem(MenuItem):

    def __init__(self, title, url, group=None, active=False, submenu_items=[]):
        super(LinkMenuItem, self).__init__(title, False, group, active, submenu_items)
        self.url = url

    def __str__(self):
        return self.title


class CollapsibleMenuItem(MenuItem):

    def __init__(self, title, url=None, group=None, active=False, submenu_items=[]):
        super(CollapsibleMenuItem, self).__init__(title, True, group, active, submenu_items)
        self.url = url


class MenuGenerator:

    default_menu_item_class = LinkMenuItem

    def __init__(self, request, site, active_groups):
        self.request = request
        self.site = site
        self.active_groups = active_groups

    def get_core(self, core_name):
        from .main import UIISCore

        core = self.site._registry.get(core_name)
        return core if isinstance(core, UIISCore) else None

    def get_menu_item(self, core_name, group=None):
        core = self.get_core(core_name)
        return core.get_menu_item(self.request, group, self.default_menu_item_class) if core else None

    def get_menu_items(self, items):
        if self.active_groups:
            group = self.active_groups[0]
        else:
            group = None

        for item in items:
            if isinstance(item, MenuItem):
                menu_item =  deepcopy(item)
                if menu_item.submenu_items:
                    menu_item.submenu_items = list(self.get_menu_items(item.submenu_items))

                yield menu_item
            else:
                menu_item = self.get_menu_item(item, group)
                if menu_item:
                    yield menu_item

    def get_menu_structure(self):
        return self.site._registry.keys()
