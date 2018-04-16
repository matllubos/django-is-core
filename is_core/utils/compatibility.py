from distutils.version import StrictVersion

import django
from django.forms.forms import BoundField as OriginalBoundField


try:
    from django.core.urlresolvers import reverse, resolve, NoReverseMatch
except ImportError:
    from django.urls import reverse, resolve, NoReverseMatch


try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    from django.db.models.loading import get_model


try:
    from django.template import Library
except ImportError:
    from django.template.base import Library


def admin_display_for_value(value):
    if StrictVersion(django.get_version()) >= StrictVersion('1.9'):
        from django.contrib.admin.utils import display_for_value

        return display_for_value(value, '-')
    else:
        try:
            from django.contrib.admin.utils import display_for_value

            return display_for_value(value)
        except ImportError:
            from django.contrib.admin.util import display_for_value

            return display_for_value(value)


def urls_wrapper(*urls):
    if StrictVersion(django.get_version()) >= StrictVersion('1.9'):
        return list(urls)
    else:
        from django.conf.urls import patterns

        return patterns('', *urls)


def get_model_name(model):
    return str(model._meta.model_name)


class BoundField(OriginalBoundField):

    def build_widget_attrs(self, attrs, widget=None):
        if StrictVersion(django.get_version()) >= StrictVersion('1.10'):
            return super(BoundField, self).build_widget_attrs(attrs, widget)
        else:
            return attrs


try:
    from django.contrib.auth import _get_backends
    get_model = apps.get_model
except ImportError:
    from django.contrib.auth import get_backends
    _get_backends = get_backends


class CompatibilityWidgetMixin:

    def build_attrs(self, base_attrs, extra_attrs=None, **kwargs):
        """
        Helper function for building an attribute dictionary.
        This is combination of the same method from Django<=1.10 and Django1.11+
        """

        attrs = dict(base_attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs


class MiddlewareMixin:

    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        response = response or self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response
