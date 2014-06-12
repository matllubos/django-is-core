from __future__ import unicode_literals

from django import template

from is_core.site import get_site_by_name, MenuGroup
from is_core import config
from is_core.utils import str_to_class
from is_core.menu import MenuItem

register = template.Library()


class MenuItemPattern():

    def __init__(self, title, pattern, show_in_menu=True, submenu_items=[], pattern_kwargs={}):
        self.title = title
        self.pattern = pattern
        self.show_in_menu = show_in_menu
        self.pattern_kwargs = pattern_kwargs


@register.inclusion_tag('menu/sub_menu.html', takes_context=True)
def submenu(context, menu_items):
    return {'menu_items': menu_items}


@register.inclusion_tag('menu/menu.html', takes_context=True)
def menu(context, site_name):
    site = get_site_by_name(site_name)
    request = context.get('request')

    active_menu_groups = context.get('active_menu_groups')

    try:
        menu_generator = str_to_class(config.MENU_GENERATOR)(request, site)
        menu_items = menu_generator.get_menu_items(menu_generator.get_menu_structure(), active_menu_groups)
    except Exception as ex:
        print ex
    context.update({'menu_items': menu_items, 'site_name': site_name})
    return context


@register.inclusion_tag('menu/bread_crumbs.html', takes_context=True)
def bread_crumbs(context):
    site_name = 'IS'
    site = get_site_by_name(site_name)
    bread_crumbs_menu_items = context.get('bread_crumbs_menu_items')

    request = context.get('request')

    active_menu_groups = context.get('active_menu_groups') or []

    menu_items = []
    items = site._registry

    menu_generator = str_to_class(config.MENU_GENERATOR)(request, site)

    for group in active_menu_groups:
        item = items.get(group)
        if item:
            if isinstance(item, MenuGroup):
                submenu_items = menu_generator.get_menu_items(item.items.values())
                url = submenu_items[0].url
                active = url == request.path or not url
                menu_items.append(MenuItem(item.verbose_name, submenu_items[0].url, active, group))
                items = item.items
            else:
                break

    for menu_item in bread_crumbs_menu_items:
        menu_items.append(menu_item)
    return {'menu_items': menu_items}
