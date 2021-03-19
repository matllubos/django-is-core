from django import template

import import_string

from is_core.config import settings
from is_core.site import get_site_by_name

register = template.Library()


@register.inclusion_tag('is_core/menu/sub_menu.html', takes_context=True)
def submenu(context, menu_items):
    return {'menu_items': menu_items}


@register.inclusion_tag('is_core/menu/menu.html', takes_context=True)
def menu(context, site_name):
    site = get_site_by_name(site_name)
    request = context.get('request')

    active_menu_groups = context.get('active_menu_groups')

    menu_generator = import_string(settings.MENU_GENERATOR)(request, site, active_menu_groups)
    menu_items = menu_generator.get_menu_items(menu_generator.get_menu_structure())
    context.update({'menu_items': menu_items, 'site_name': site_name})
    return context


@register.inclusion_tag('is_core/menu/bread_crumbs.html', takes_context=True)
def bread_crumbs(context):
    bread_crumbs_menu_items = context.get('bread_crumbs_menu_items')

    menu_items = []

    for menu_item in bread_crumbs_menu_items or []:
        menu_items.append(menu_item)
    return {'menu_items': menu_items}


@register.simple_tag
def header_image():
    return settings.HEADER_IMAGE


@register.simple_tag
def environment():
    return settings.ENVIRONMENT
