from is_core.site import MenuGroup


class MenuItem(object):

    def __init__(self, title, active, collapsible, group, submenu_items=[]):
        self.title = title
        self.collapsible = collapsible
        self.submenu_items = submenu_items
        self.group = group
        self.active = active


class LinkMenuItem(MenuItem):

    def __init__(self, title, url, active, group=None, submenu_items=[]):
        super(LinkMenuItem, self).__init__(title, active, False, group, submenu_items)
        self.url = url

    def __unicode__(self):
        return self.title


class CollapsibleMenuItem(MenuItem):

    def __init__(self, title, active, group=None, submenu_items=[]):
        super(CollapsibleMenuItem, self).__init__(title, active, True, group, submenu_items)


class MenuGenerator(object):

    def __init__(self, request, site):
        self.request = request
        self.site = site

    def get_menu_items(self, items, active_groups=()):
        menu_items = []
        if active_groups:
            group, child_groups = active_groups[0], active_groups[1:]
        else:
            group = child_groups = None

        for item in items:
            if isinstance(item, MenuGroup):
                submenu_items = self.get_menu_items(item.items.values(), child_groups)
                if submenu_items:
                    menu_items.append(MenuItem(item.verbose_name, submenu_items[0].url,
                                               item.name == group, item.name))
            else:
                item = self.site._registry[item]
                menu_item = item.get_menu_item(self.request, group)
                if menu_item:
                    menu_items.append(menu_item)
        return menu_items

    def get_menu_structure(self):
        return self.site._registry.keys()
