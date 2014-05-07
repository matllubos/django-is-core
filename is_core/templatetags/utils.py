from __future__ import unicode_literals

import json as serializer
import os

from django.template.base import Library

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
