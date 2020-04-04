import json as serializer
import os

from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.template import Library

from is_core.utils import display_object_data as utils_display_object_data


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


@register.simple_tag(takes_context=True)
def display_object_data(context, obj, field_name):
    return utils_display_object_data(obj, field_name, context.get('request'))
