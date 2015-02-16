from __future__ import unicode_literals

import re
import logging

from django.core.urlresolvers import reverse, resolve, Resolver404
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import SortedDict

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
        kwargs = (kwargs or {}).copy()
        if obj:
            kwargs.update(self._get_try_kwarg(obj))
        return reverse(self.pattern, kwargs=kwargs)

    def get_view_dispatch(self):
        raise NotImplementedError

    def get_view(self, request, args=None, kwargs=None):
        raise NotImplementedError

    def get_url(self):
        url_pattern = self.url_pattern
        if self.url_prefix:
            url_pattern = self.url_pattern
            if url_pattern.startswith('^'):
                url_pattern = url_pattern[1:]
            url_pattern = '^%s%s' % (self.url_prefix, url_pattern)
        return url(url_pattern, self.get_view_dispatch(), name=self.name)

    def __getattr__(self, name):
        for regex in (r'_check_(\w+)_permission', r'can_call_(\w+)'):
            m = re.match(regex, name)
            if m:
                def _call(request, obj=None, view_kwargs=None, **kwargs):
                    view_kwargs = (view_kwargs or {}).copy()
                    if obj:
                        view_kwargs.update(self._get_try_kwarg(obj))

                    view = self.get_view(request, None, view_kwargs)
                    return getattr(view, name)(**kwargs)
                return _call
        raise AttributeError("%r object has no attribute %r" % (self.__class__, name))


class UIPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, view_class, core=None):
        super(UIPattern, self).__init__(name, site_name, url_pattern, core)
        self.view_class = type(str(get_new_class_name(name, view_class)), (view_class,), {})
        if core:
            self.view_class.__init_core__(core, self)

    def get_view(self, request, args=None, kwargs=None):
        view = self.view_class()
        if args:
            view.args = args
        if kwargs:
            view.kwargs = kwargs
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

    def get_view(self, request, args=None, kwargs=None):
        view = self.resource_class(request)
        if args:
            view.args = args
        if kwargs:
            view.kwargs = kwargs
        return view

    def get_view_dispatch(self):
        dispatch = self.resource_class.as_view(allowed_methods=self.methods)
        if self.resource_class.login_required:
            return rest_login_required(dispatch)
        return dispatch

    def get_allowed_methods(self, request, obj):
        return self.resource_class(request).get_allowed_methods(obj, self.methods)


class DoubleRestPattern(object):

    def __init__(self, resource_class, pattern_class, core):
        self.resource_class = resource_class
        self.pattern_class = pattern_class
        self.core = core

    @property
    def patterns(self):
        result = SortedDict()
        result['api-resource'] = self.pattern_class(
            'api-resource-%s' % self.core.get_menu_group_pattern_name(), self.core.site_name, r'^/(?P<pk>[-\w]+)/?$',
            self.resource_class, self.core, ('get', 'put', 'delete')
        )
        result['api'] = self.pattern_class(
            'api-%s' % self.core.get_menu_group_pattern_name(), self.core.site_name, r'^/?$', self.resource_class, self.core,
             ('get', 'post')
        )
        return result

