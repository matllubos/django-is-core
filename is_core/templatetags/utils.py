from __future__ import unicode_literals

import json as serializer
import os

from django.template.base import Library
from django.utils.safestring import mark_safe
from django.utils.html import escape

try:
    from django.contrib.admin.utils import display_for_value as admin_display_for_value
except ImportError:
    from django.contrib.admin.util import display_for_value as admin_display_for_value

from is_core.utils import display_for_value as utils_display_for_value

register = Library()


@register.filter
def to_list(value):
    if isinstance(value, (list, tuple)):
        return value

    return [value]


@register.filter
def json(value):
    return serializer.dumps(value)


@register.filter
def filename(value):
    return os.path.basename(value.file.name)


def display_for_value(value):
    if isinstance(value, dict):
        return mark_safe('<ul>%s</ul>' % '\n'.join('<li>%s: %s</li>' % (escape(key), escape(val))
                                                   for key, val in value.items()))
    else:
        return utils_display_for_value(value)


@register.filter
def display_object_data(obj, field_name):
    humanize_method_name = 'get_%s_humanized' % field_name
    display_method_name = 'get_%s_display' % field_name
    if hasattr(getattr(obj, humanize_method_name, None), '__call__'):
        value = getattr(obj, humanize_method_name)()
    elif hasattr(getattr(obj, display_method_name, None), '__call__'):
        value = getattr(obj, display_method_name)()
    elif hasattr(obj, field_name):
        value = getattr(obj, field_name)
    elif isinstance(obj, dict) and field_name in obj:
        value = obj.get(field_name)

    if hasattr(value, '__call__'):
        value = value()

    return utils_display_for_value(value)
