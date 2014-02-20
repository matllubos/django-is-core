from django.core.urlresolvers import reverse
from django.conf.urls import url


class ViewPattern(object):

    def __init__(self, name, site_name, url_pattern, view):
        self.url_pattern = url_pattern
        self.name = name
        self.site_name = site_name
        self.view = view

    @property
    def pattern(self):
        return '%s:%s' % (self.site_name, self.name)

    def _get_try_kwarg(self, obj):
        if'(?P<pk>\d+)' in self.url_pattern:
            return {'pk': obj.pk}
        return {}

    def get_url_string(self, obj):
        try:
            return reverse(self.pattern, kwargs=self._get_try_kwarg(obj))
        except:
            pass

    def get_url(self):
        return url(self.url_pattern, self.view, name=self.name)


class UIPattern(ViewPattern):
    pass


class RestPattern(ViewPattern):

    def __init__(self, name, site_name, url_pattern, resource, methods=()):
        super(RestPattern, self).__init__(name, site_name, url_pattern, resource)
        self.resource = resource
        self.methods = methods

    def get_allowed_methods(self, user, obj):
        methods = self.resource.handler.get_allowed_methods(user, obj.pk)
        return set(methods) & set(self.methods)
