from __future__ import unicode_literals

import logging

from django.core.urlresolvers import reverse, resolve, Resolver404
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from is_core.utils import get_new_class_name
from is_core.auth import rest_login_required


logger = logging.getLogger('is-core')

patterns = {}


def reverse_ui_view(name, request):
    pattern = patterns.get(name)
    if isinstance(pattern, UIPattern):
        return pattern.get_view(request)


def reverse_pattern(name):
    return patterns.get(name)


def pattern_from_request(request):
    return reverse_pattern(resolve(request.path).url_name)


def is_rest_request(request):
    try:
        return isinstance(pattern_from_request(request), RestPattern)
    except Resolver404:
        return False


class Pattern(object):

    send_in_rest = True

    def __init__(self, name):
        self.name = name
        self.url_prefix = None
        self._register()

    def _register(self):
        if self.name in patterns:
            logger.warning('Pattern with name %s has been registered yet' % self.name)
        patterns[self.name] = self

    def get_url_string(self, request, obj=None, kwargs=None):
        raise NotImplemented

    def get_url(self):
        return None


class ViewPattern(Pattern):

    def __init__(self, name, site_name, url_pattern, core):
        super(ViewPattern, self).__init__(name)
        self.url_pattern = url_pattern
        self.site_name = site_name
        self.core = core
        self.url_prefix = self.get_url_prefix()

    def get_url_prefix(self):
        if self.core:
            return self.core.get_url_prefix()

    @property
    def pattern(self):
        return '%s:%s' % (self.site_name, self.name)

    def _get_try_kwarg(self, obj):
        if'(?P<pk>[-\w]+)' in self.url_pattern or '(?P<pk>\d+)' in self.url_pattern:
            return {'pk': obj.pk}
        return {}

    def get_url_string(self, request, obj=None, kwargs=None):
        kwargs = kwargs or {}
        if obj:
            kwargs.update(self._get_try_kwarg(obj))
        return reverse(self.pattern, kwargs=kwargs)

    def get_view_dispatch(self):
        raise NotImplemented

    def get_url(self):
        url_pattern = self.url_pattern
        if self.url_prefix:
            url_pattern = self.url_pattern
            if url_pattern.startswith('^'):
                url_pattern = url_pattern[1:]
            url_pattern = '^%s%s' % (self.url_prefix, url_pattern)
        return url(url_pattern, self.get_view_dispatch(), name=self.name)


class UIPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, view_class, core=None):
        super(UIPattern, self).__init__(name, site_name, url_pattern, core)
        self.view_class = type(str(get_new_class_name(name, view_class)), (view_class,), {})
        if core:
            self.view_class.__init_core__(core, self)

    def get_view(self, request):
        view = self.view_class()
        view.request = request
        return view

    def get_view_dispatch(self):
        dispatch = self.view_class.as_view()
        if self.view_class.login_required:
            return login_required(dispatch)
        return dispatch


class RestPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, resource_class, core=None, methods=None):
        super(RestPattern, self).__init__(name, site_name, url_pattern, core)
        self.resource_class = resource_class
        self.methods = methods
        if core:
            self.resource_class.__init_core__(core, self)

    def get_url_prefix(self):
        url_prefix = super(RestPattern, self).get_url_prefix()
        if url_prefix:
            return 'api/%s' % url_prefix

    def get_view(self, request):
        return self.resource_class(request)

    def get_view_dispatch(self):
        dispatch = self.resource_class.as_view(allowed_methods=self.methods)
        if self.resource_class.login_required:
            return rest_login_required(dispatch)
        return dispatch

    def get_allowed_methods(self, request, obj):
        return self.resource_class(request).get_allowed_methods(obj, self.methods)
