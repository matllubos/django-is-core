from collections import OrderedDict

from django.conf.urls import url, include
from django.template.defaultfilters import lower
from django.core.exceptions import ImproperlyConfigured

from is_core.config import settings
from is_core.utils.compatibility import urls_wrapper

from .utils import str_to_class
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
    model_label = lower('%s.%s' % (model._meta.app_label, model._meta.object_name))
    return registered_model_cores.get(model_label)


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
        if (hasattr(generic_core, 'model')):
            model_label = lower('%s.%s' % (generic_core.model._meta.app_label, generic_core.model._meta.object_name))
            registered_model_cores[model_label] = generic_core
        registered_cores.append(generic_core)
        return generic_core

    @property
    def urls(self):
        return self.get_urls(), self.name

    def _set_items_urls(self, items, urlpatterns):
        for item in items:
            urls = item.get_urls()
            if urls:
                urlpatterns += urls_wrapper(url(r'^', include(urls)))

    def get_urls(self):
        urlpatterns = urls_wrapper()
        if settings.AUTH_LOGIN_VIEW:
            urlpatterns += urls_wrapper(
                url(r'^{}$'.format(settings.LOGIN_URL[1:]), str_to_class(settings.AUTH_LOGIN_VIEW).as_view(
                    form_class=str_to_class(settings.AUTH_FORM_CLASS)), name='login'),
            )

        if settings.AUTH_LOGOUT_VIEW:
            urlpatterns += urls_wrapper(
                url(r'^{}$'.format(settings.LOGOUT_URL[1:]),
                    str_to_class(settings.AUTH_LOGOUT_VIEW).as_view(), name='logout'),
            )

        if settings.AUTH_RESOURCE_CLASS:
            auth_resource_class = str_to_class(settings.AUTH_RESOURCE_CLASS)
            auth_resource_class.form_class = str_to_class(settings.AUTH_FORM_CLASS)
            pattern = RESTPattern('api-login', self.name, settings.LOGIN_API_URL[1:],
                                  auth_resource_class)
            urlpatterns += urls_wrapper(pattern.get_url())

        pattern = RESTPattern('api', self.name, r'api/', EntryPointResource)
        urlpatterns += urls_wrapper(pattern.get_url())

        self._set_items_urls(self._registry.values(), urlpatterns)
        return urlpatterns


site = ISSite()


def get_cores():
    return site._registry.values()


def get_core(name):
    return site._registry[name]
