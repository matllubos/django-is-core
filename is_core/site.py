"""
Registration cores to concrete site.
Contains helpers for getting core of a model.
"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.template.defaultfilters import lower
from django.core.exceptions import ImproperlyConfigured

from . import config
from .utils import str_to_class
from .loading import get_cores
from .patterns import RESTPattern
from .auth_token.auth_resource import AuthResource
from .rest.resource import EntryPointResource


sites = {}
registered_model_cores = {}
registered_cores = []


def get_site_by_name(name):
    """
    Return site according to name (default is IS)
    """
    return sites.get(name)


def get_model_core(model):
    """
    Return core view of given model or None
    """
    model_label = lower('%s.%s' % (model._meta.app_label, model._meta.object_name))
    return registered_model_cores.get(model_label)


class ISSite(object):

    def __init__(self, name='IS'):
        self.name = name
        self.app_name = name
        sites[name] = self
        self._registry = self._init_items()

    def _init_items(self):
        out = OrderedDict()

        for core in get_cores():
            generic_core = self.register(core(self.name, []))
            if generic_core.menu_group in out:
                raise ImproperlyConfigured('Duplicate cores with group: "%s"' % generic_core.menu_group)
            out[generic_core.menu_group] = generic_core
        return out

    def register(self, generic_core):
        if (hasattr(generic_core, 'model')):
            model_label = lower('%s.%s' % (generic_core.model._meta.app_label, generic_core.model._meta.object_name))
            registered_model_cores[model_label] = generic_core
        registered_cores.append(generic_core)
        return generic_core

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name

    def _set_items_urls(self, items, urlpatterns):
        for item in items:
            urlpatterns += patterns('', url(r'^', include(item.get_urls())))

    def get_urls(self):
        LoginView = str_to_class(config.IS_CORE_AUTH_LOGIN_VIEW)
        LogoutView = str_to_class(config.IS_CORE_AUTH_LOGOUT_VIEW)
        urlpatterns = patterns('',
            url(r'^%s$' % config.IS_CORE_LOGIN_URL[1:],
                LoginView.as_view(form_class=str_to_class(config.IS_CORE_AUTH_FORM_CLASS)),
                name='login'),
            url(r'^%s$' % config.IS_CORE_LOGOUT_URL[1:], LogoutView.as_view(), name='logout')
        )

        if config.IS_CORE_AUTH_USE_TOKENS:
            AuthResource.form_class = str_to_class(config.IS_CORE_AUTH_FORM_CLASS)
            pattern = RESTPattern('api-login', self.name, r'%s' % config.IS_CORE_LOGIN_API_URL[1:], AuthResource)
            urlpatterns += patterns('', pattern.get_url())

        pattern = RESTPattern('api', self.name, r'api/$', EntryPointResource)
        urlpatterns += patterns('', pattern.get_url())

        self._set_items_urls(self._registry.values(), urlpatterns)
        return urlpatterns

site = ISSite()


def get_core(name):
    return site._registry[name]
