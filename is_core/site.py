from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import lower

from .utils import str_to_class
from . import config
from .loading import get_cores
from .patterns import RestPattern
from .auth_token.auth_resource import AuthResource


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
        self._registry = self._init_items()

    def _init_items(self):
        out = SortedDict()

        for core in get_cores():
            generic_core = self.register(core(self.name, []))
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
                                    url(r'^%s$' % settings.LOGIN_URL[1:],
                                        LoginView.as_view(form_class=str_to_class(config.AUTH_FORM_CLASS)),
                                        name='login'),
                                    url(r'^%s$' % settings.LOGOUT_URL[1:], LogoutView.as_view(), name='logout'),
                               )


        if config.AUTH_USE_TOKENS:
            resource_kwargs = {
                  'form_class': str_to_class(config.AUTH_FORM_CLASS)
            }
            pattern = RestPattern('api-login', self.name, r'^/api/login/?$', AuthResource, resource_kwargs)
            urlpatterns += patterns('', pattern.get_url())

        self._set_items_urls(self._registry.values(), urlpatterns)
        return urlpatterns

site = ISSite()
