from __future__ import unicode_literals

import json as serializer
import os

from django.template.base import Library
from django.contrib.admin.util import display_for_value as admin_display_for_value
from django.utils.safestring import mark_safe
from django.utils.html import escape

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
