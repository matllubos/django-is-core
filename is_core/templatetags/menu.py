from __future__ import unicode_literals

from django import template
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from is_core.site import get_site_by_name, MenuGroup
from is_core import config

register = template.Library()


class MenuItem():

    def __init__(self, title, url, active, group=None, submenu_items=[]):
        self.title = title
        self.url = url
        self.active = active
        self.group = group
        self.submenu_items = submenu_items

    def __unicode__(self):
        return self.title


def get_menu_items(request, items, active_groups=()):
    menu_items = []
    if active_groups:
        group, child_groups = active_groups[0], active_groups[1:]
    else:
        group = child_groups = None

    for item in items:
        if isinstance(item, MenuGroup):
            submenu_items = get_menu_items(request, item.items.values(), child_groups)
            if submenu_items:
                menu_items.append(MenuItem(item.verbose_name, submenu_items[0].url,
                                            item.name == group, item.name))
        else:
            if not item.get_show_in_menu(request):
                continue

            menu_items.append(MenuItem(item.verbose_name_plural, item.menu_url(),
                                       group == item.menu_group, item.menu_group))
    return menu_items


@register.inclusion_tag('menu/sub_menu.html', takes_context=True)
def submenu(context, menu_items):
    return {'menu_items': menu_items}


@register.inclusion_tag('menu/menu.html', takes_context=True)
def menu(context, site_name):
    site = get_site_by_name(site_name)

    request = context.get('request')

    active_menu_groups = context.get('active_menu_groups')
    menu_items = get_menu_items(request, site._registry.values(), active_menu_groups)
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
    if config.HOME_IN_BREADCRUMB:
        index_url = reverse('%s:index' % site_name)
        index_active = request.path == index_url
        menu_items.append(MenuItem(_('Home'), index_url, index_active))

    items = site._registry

    for group in active_menu_groups:
        item = items.get(group)
        if item:
            if isinstance(item, MenuGroup):
                submenu_items = get_menu_items(request, item.items.values())
                url = submenu_items[0].url
                active = url == request.path or not url
                menu_items.append(MenuItem(item.verbose_name, submenu_items[0].url, active, group))
                items = item.items
            else:
                break

    for menu_item in bread_crumbs_menu_items:
        menu_items.append(menu_item)
    return {'menu_items': menu_items}
