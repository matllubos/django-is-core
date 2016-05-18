from __future__ import unicode_literals

import json as serializer
import os

from django.utils.safestring import mark_safe
from django.utils.html import escape

from is_core.utils import display_for_value as utils_display_for_value
from is_core.utils.compatibility import Library


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
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        return display_object_data(getattr(obj, current_field_name), next_field_name)
    else:
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
        else:
            raise AttributeError('Field or method %s does not exists' % field_name)
        if hasattr(value, '__call__'):
            value = value()
        return utils_display_for_value(value)
