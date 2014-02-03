from django import template
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from is_core.site import get_site_by_name

register = template.Library()


class MenuItem():

    def __init__(self, title, url, active, submenu_items=[]):
        self.title = title
        self.url = url
        self.active = active
        self.submenu_items = submenu_items


def second_menu_items(request, site, account, environment, active_menu_group, active_menu_subgroup):
    menu_items = []
    for view in site._registry[active_menu_group].views.values():
        # TODO: Every application shoud have own index
        if not view.get_show_in_menu(request):
            continue

        menu_items.append(MenuItem(view.menu_verbose_name, view.menu_url(account, environment),
                                    active_menu_subgroup == view.menu_subgroup))
    return menu_items


def main_menu_items(request, site, account, environment, active_menu_group, active_menu_subgroup):
    menu_items = []
    for group_name, group in site._registry.items():
        first_view = None

        for view in group.views.values():
            if view.get_show_in_menu(request):
                first_view = view
                break

        # TODO: Every application shoud have own index
        if first_view:
            active = group_name == active_menu_group
            submenu_items = active and second_menu_items(request, site, account, environment, active_menu_group,
                                                         active_menu_subgroup) or []
            menu_items.append(MenuItem(group.name, first_view.menu_url(account, environment),
                                        group_name == active_menu_group, submenu_items))
    return menu_items


@register.inclusion_tag('menu/menu.html', takes_context=True)
def menu(context, site_name):
    site = get_site_by_name(site_name)

    request = context.get('request')
    environment = context.get('environment')
    account = context.get('account')

    active_menu_group = context.get('active_menu_group')
    active_menu_subgroup = context.get('active_menu_subgroup')

    menu_items = []

    if environment and account:
        menu_items = main_menu_items(request, site, account, environment, active_menu_group, active_menu_subgroup)
    return {'menu_items': menu_items, 'environment': environment, 'account': account, 'site_name': site_name}


@register.inclusion_tag('menu/bread_crumbs.html', takes_context=True)
def bread_crumbs(context):
    site_name = context.get('site_name')
    site = get_site_by_name(site_name)

    request = context.get('request')
    environment = context.get('environment')
    account = context.get('account')

    active_menu_group = context.get('active_menu_group')
    active_menu_subgroup = context.get('active_menu_subgroup')

    menu_items = []

    if environment and account:
        index_url = reverse('%s:index' % site_name, args=(account, environment))
        index_active = request.path == index_url
        menu_items = [MenuItem(_('Home'), index_url, index_active)]

        if active_menu_group:
            for verbose_name, pattern in site._registry[active_menu_group].views[active_menu_subgroup].bread_crumbs_url_names(context):
                url = pattern and reverse(pattern, args=(account, environment)) or None
                active = url == request.path or not url

                menu_items.append(MenuItem(verbose_name, url, active))

    return {'menu_items': menu_items, 'environment': environment, 'account': account}
