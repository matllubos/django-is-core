from collections import OrderedDict

from django.db.models import Model
from django.conf.urls import url, include
from django.template.defaultfilters import lower
from django.core.exceptions import ImproperlyConfigured

import import_string

from is_core.config import settings

from .loading import get_cores
from .patterns import RESTPattern
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
    return registered_model_cores.get(model)


class ISSite:

    def __init__(self, name='IS'):
        self.name = name
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
        if getattr(generic_core, 'register_model', False):
            registered_model_cores[generic_core.model] = generic_core
        registered_cores.append(generic_core)
        return generic_core

    @property
    def urls(self):
        return self.get_urls(), self.name

    def _set_items_urls(self, items, urlpatterns):
        for item in items:
            urls = item.get_urls()
            if urls:
                urlpatterns += [url(r'^', include(urls))]

    def get_urls(self):
        urlpatterns = []
        if settings.AUTH_LOGIN_VIEW:
            urlpatterns.append(
                url(r'^{}$'.format(settings.LOGIN_URL[1:]), import_string(settings.AUTH_LOGIN_VIEW).as_view(
                    form_class=import_string(settings.AUTH_FORM_CLASS)), name='login')
            )

        if settings.AUTH_LOGOUT_VIEW:
            urlpatterns.append(
                url(r'^{}$'.format(settings.LOGOUT_URL[1:]),
                    import_string(settings.AUTH_LOGOUT_VIEW).as_view(), name='logout')
            )

        if settings.AUTH_RESOURCE_CLASS:
            auth_resource_class = import_string(settings.AUTH_RESOURCE_CLASS)
            auth_resource_class.form_class = import_string(settings.AUTH_FORM_CLASS)
            pattern = RESTPattern('api-login', self.name, settings.LOGIN_API_URL[1:],
                                  auth_resource_class)
            urlpatterns.append(pattern.get_url())

        if settings.AUTH_LOGIN_CODE_VERIFICATION_VIEW:
            urlpatterns.append(
                url(r'^{}$'.format(settings.CODE_VERIFICATION_URL[1:]),
                    import_string(settings.AUTH_LOGIN_CODE_VERIFICATION_VIEW).as_view(), name='code-verification-login')
            )

        pattern = RESTPattern('api', self.name, r'api/', EntryPointResource)
        urlpatterns.append(pattern.get_url())

        self._set_items_urls(self._registry.values(), urlpatterns)
        return urlpatterns


site = ISSite()


def get_cores():
    return site._registry.values()


def get_core(name):
    return site._registry[name]
