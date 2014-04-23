from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import lower

from is_core.utils import str_to_class
from is_core import config
from is_core.rest.resource import RestResource
from is_core.auth_token.auth_handler import AuthHandler


sites = {}
registered_model_views = {}
registered_views = []


def get_site_by_name(name):
    """
    Return site according to name (default is IS)
    """
    return sites.get(name)


def get_model_view(model):
    """
    Return core view of given model or None
    """
    model_label = lower('%s.%s' % (model._meta.app_label, model._meta.object_name))
    return registered_model_views.get(model_label)


class NoMenuGroup(Exception):
    pass


class MenuGroup(object):

    def __init__(self, name, verbose_name, items):
        self.name = name
        self.verbose_name = verbose_name
        self.items = items


class ISSite(object):

    def __init__(self, name='IS'):
        self.name = name
        self.app_name = name
        sites[name] = self
        self._registry = self._init_items([config.HOME_IS_CORE] + list(settings.MENU_GROUPS))

    def _init_items(self, items, groups=()):
        out = SortedDict()

        for item in items:
            if isinstance(item, (list, tuple)):
                name, verbose_name, subitems = item
                out[name] = MenuGroup(name, verbose_name, self._init_items(subitems, groups + (name,)))
            else:
                generic_core = self.register(str_to_class(item)(self.name, groups))
                out[generic_core.menu_group] = generic_core
        return out

    def register(self, generic_core):
        if (hasattr(generic_core, 'model')):
            model_label = lower('%s.%s' % (generic_core.model._meta.app_label, generic_core.model._meta.object_name))
            registered_model_views[model_label] = generic_core
        registered_views.append(generic_core)
        return generic_core

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name

    def _set_items_urls(self, items, urlpatterns):
        for item in items:
            if isinstance(item, MenuGroup):
                self._set_items_urls(item.items.values(), urlpatterns)
            else:
                urlpatterns += patterns('',
                    url(r'^%s' % (item.get_url_prefix()),
                            include(item.get_urls())
                        )
                )

    def get_urls(self):
        LoginView = str_to_class(config.AUTH_LOGIN_VIEW)
        LogoutView = str_to_class(config.AUTH_LOGOUT_VIEW)
        urlpatterns = patterns('',
                                    url(r'^login/$', LoginView.as_view(form_class=str_to_class(config.AUTH_FORM_CLASS)),
                                        name='login'),
                                    url(r'^logout/$', LogoutView.as_view(), name='logout'),
                               )

        if config.AUTH_USE_TOKENS:
            login_resource = RestResource(handler=AuthHandler, form_class=str_to_class(config.AUTH_FORM_CLASS))
            urlpatterns += patterns('', url(r'^api/login/$', login_resource, name='api-login'))

        self._set_items_urls(self._registry.values(), urlpatterns)
        return urlpatterns

site = ISSite()
