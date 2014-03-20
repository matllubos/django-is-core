from django.core.urlresolvers import reverse
from django.conf.urls import url
from is_core.rest.resource import DynamicRestHandlerResource


class ViewPattern(object):

    def __init__(self, name, site_name, url_pattern, core):
        self.url_pattern = url_pattern
        self.name = name
        self.site_name = site_name
        self.core = core

    @property
    def pattern(self):
        return '%s:%s' % (self.site_name, self.name)

    def _get_try_kwarg(self, obj):
        if'(?P<pk>[-\w]+)' in self.url_pattern or '(?P<pk>\d+)' in self.url_pattern:
            return {'pk': obj.pk}
        return {}

    def get_url_string(self, obj):
        return reverse(self.pattern, kwargs=self._get_try_kwarg(obj))

    def get_view(self):
        raise NotImplemented

    def get_url(self):
        return url(self.url_pattern, self.get_view(), name=self.name)


class UIPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, view, core):
        super(UIPattern, self).__init__(name, site_name, url_pattern, core)
        self.view = view

    def get_view(self):
        if self.view.login_required:
            return self.view.as_wrapped_view(core=self.core)
        else:
            return self.view.as_view(core=self.core)


class RestPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, resource, core, methods=None):
        super(RestPattern, self).__init__(name, site_name, url_pattern, core)
        self.resource = resource
        self.methods = methods

    def get_view(self):
        return self.resource

    def get_allowed_methods(self, request, obj):
        methods = self.resource.handler.get_allowed_methods(request, obj.pk)
        if self.methods is not None:
            return set(methods) & set(self.methods)
        return set(methods)


class DynamicRestPattern(RestPattern):

    def __init__(self, name, site_name, url_pattern, handler, core, methods=None):
        resource = DynamicRestHandlerResource(handler_class=handler, core=core)
        super(DynamicRestPattern, self).__init__(name, site_name, url_pattern, resource, core, methods=methods)

