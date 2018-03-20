import json as serializer
import os

from django.utils.safestring import mark_safe
from django.utils.html import escape

from is_core.utils import display_object_data as utils_display_object_data
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


@register.filter
def display_object_data(obj, field_name):
    return utils_display_object_data(obj, field_name)
