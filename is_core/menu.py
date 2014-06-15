
class MenuItem(object):

    def __init__(self, title, collapsible, group, active=False, submenu_items=[]):
        self.title = title
        self.collapsible = collapsible
        self.submenu_items = submenu_items
        self.group = group
        self.active = active


class LinkMenuItem(MenuItem):

    def __init__(self, title, url, group=None, active=False, submenu_items=[]):
        super(LinkMenuItem, self).__init__(title, False, group, active, submenu_items)
        self.url = url

    def __unicode__(self):
        return self.title


class CollapsibleMenuItem(MenuItem):

    def __init__(self, title, url=None, group=None, active=False, submenu_items=[]):
        super(CollapsibleMenuItem, self).__init__(title, True, group, active, submenu_items)
        self.url = url


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
            if isinstance(item, MenuItem):
                menu_items.append(item)
            else:
                item = self.site._registry[item]
                menu_item = item.get_menu_item(self.request, group)
                if menu_item:
                    menu_items.append(menu_item)
        return menu_items

    def get_menu_structure(self):
        return self.site._registry.keys()
