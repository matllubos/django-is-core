from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import lower

from class_based_auth_views.views import LoginView

from is_core.generic_views import HomeView
from is_core.generic_views.auth_views import LogoutView


sites = {}
registered_model_views = {}
registered_views = []


def get_site_by_name(name):
    return sites.get(name)


def get_model_view(model):
    model_label = lower('%s.%s' % (model._meta.app_label, model._meta.object_name))
    return registered_model_views.get(model_label)


class NoMenuGroup(Exception):
    pass


class MenuGroup(object):

    def __init__(self, name):
        self.name = name
        self.views = SortedDict()


class ISSite(object):

    def __init__(self, name='IS'):
        self._registry = SortedDict([(group[0], MenuGroup(group[1]))\
                                     for group in settings.MENU_GROUPS.get(name)])
        self.name = name
        self.app_name = name
        sites[name] = self

    def register(self, universal_view_class):
        universal_view = universal_view_class(self.name)
        if not universal_view.menu_group in self._registry.keys():
            raise NoMenuGroup('MENU_GROUPS must contains %s for site %s' % (universal_view.menu_group, self.name))

        self._registry[universal_view.menu_group].views[universal_view.menu_subgroup] = universal_view
        if (hasattr(universal_view, 'model')):
            model_label = lower('%s.%s' % (universal_view.model._meta.app_label, universal_view.model._meta.object_name))
            registered_model_views[model_label] = universal_view
        registered_views.append(universal_view)

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name

    def get_urls(self):
        urlpatterns = patterns('',
                                    # TODO: environment must exist
                                    url(r'^/?$',
                                        login_required(HomeView.as_view(site_name=self.name),
                                                       login_url='%s:login' % self.name), name="index"),
                                    url(r'^login/$', LoginView.as_view(), name="login"),
                                    url(r'^logout/$', LogoutView.as_view(), name="logout"),
                               )

        for group_name, menu_group in self._registry.iteritems():
            for subgroup_name, persoo_view in menu_group.views.iteritems():
                urlpatterns += patterns('',
                    url(r'^%s/%s' % (group_name, subgroup_name),
                            include(persoo_view.get_urls())
                        )
                )
        return urlpatterns

site = ISSite()
