from __future__ import unicode_literals

import logging

from django.core.urlresolvers import reverse
from django.conf.urls import url

# from is_core.rest.resource import DynamicRestHandlerResource
from is_core.utils import get_new_class_name


logger = logging.getLogger('is-core')

patterns = {}


def reverse_ui_view(name):
    pattern = patterns.get(name)
    if isinstance(pattern, UIPattern):
        return pattern.view


def reverse_pattern(name):
    return patterns.get(name)


class Pattern(object):

    def __init__(self, name):
        self.name = name
        self._register()

    def _register(self):
        if self.name in patterns:
            logger.warning('Pattern with name %s has been registered yet' % self.name)
        patterns[self.name] = self

    def get_url_string(self, obj=None, kwargs=None):
        raise NotImplemented

    def get_url(self):
        return None


class ViewPattern(Pattern):

    def __init__(self, name, site_name, url_pattern, core):
        super(ViewPattern, self).__init__(name)
        self.url_pattern = url_pattern
        self.site_name = site_name
        self.core = core

    @property
    def pattern(self):
        return '%s:%s' % (self.site_name, self.name)

    def _get_try_kwarg(self, obj):
        if'(?P<pk>[-\w]+)' in self.url_pattern or '(?P<pk>\d+)' in self.url_pattern:
            return {'pk': obj.pk}
        return {}

    def get_url_string(self, obj=None, kwargs=None):
        kwargs = kwargs or {}
        if obj:
            kwargs.update(self._get_try_kwarg(obj))
        return reverse(self.pattern, kwargs=kwargs)

    def get_view(self):
        raise NotImplemented

    def get_url(self):
        return url(self.url_pattern, self.get_view(), name=self.name)


class UIPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, view, core=None):
        super(UIPattern, self).__init__(name, site_name, url_pattern, core)
        self.view = type(str(get_new_class_name(name, view)), (view,), {})
        if core:
            self.view.__init_core__(core, self)

    def get_view(self):
        if self.view.login_required:
            return self.view.as_wrapped_view()
        else:
            return self.view.as_view()


class RestPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, resource, methods=None, core=None):
        super(RestPattern, self).__init__(name, site_name, url_pattern, core)
        self.resource = resource
        self.methods = methods

    def get_view(self):
        if self.resource.login_required:
            return self.resource.as_wrapped_view(self.methods)
        else:
            return self.resource.as_view()

    def get_allowed_methods(self, user, obj):
        return self.resource.get_allowed_methods(user, obj, self.methods)
