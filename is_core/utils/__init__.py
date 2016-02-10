from __future__ import unicode_literals

import re
import sys
import types
import inspect

from django.http.request import QueryDict
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks, conditional_escape
from django.db.models.fields.related import ManyToManyRel, ForeignKey
from django.db.models.base import Model

from chamber.utils import get_class_method

from is_core.forms.forms import ReadonlyValue


def str_to_class(class_string):
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), str(class_name))
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_new_class_name(prefix, klass):
    prefix = prefix.replace('-', ' ').title()
    prefix = re.sub(r'\s+', '', prefix)
    return prefix + klass.__name__


def flatten_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    field_names = []
    for _, opts in fieldsets:
        if opts.get('fieldsets'):
            field_names += flatten_fieldsets(opts.get('fieldsets'))
        else:
            for field in opts.get('fields', ()):
                if isinstance(field, (list, tuple)):
                    field_names.extend(field)
                else:
                    field_names.append(field)
    return field_names


def get_callable_value_or_value(callable_value, fun_kwargs):
    if hasattr(callable_value, '__call__'):
        maybe_kwargs_names = inspect.getargspec(callable_value)[0][1:]
        maybe_kwargs = {}

        for arg_name in maybe_kwargs_names:
            if arg_name in fun_kwargs:
                maybe_kwargs[arg_name] = fun_kwargs[arg_name]

        if len(maybe_kwargs_names) == len(maybe_kwargs):
            return callable_value(**maybe_kwargs)
        else:
            raise AttributeError
    else:
        return callable_value

def field_humanized_value(instance, field):
    humanize_method_name = 'get_%s_humanized' % field.name
    if hasattr(getattr(instance, humanize_method_name, None), '__call__'):
        return getattr(instance, humanize_method_name)()


def field_display_value(instance, field):
    display_method_name = 'get_%s_display' % field.name
    if hasattr(getattr(instance, display_method_name, None), '__call__'):
        return getattr(instance, display_method_name)()


def field_value(instance, field, value, fun_kwargs):
    if isinstance(field.rel, ManyToManyRel) and value is not None and hasattr(getattr(value, 'all'), '__call__'):
        return [obj for obj in value.all()]
    elif isinstance(field, ForeignKey):
        return value

    return get_callable_value_or_value(value, fun_kwargs)


def field_widget(instance, field):
    from is_core.forms.widgets import ModelObjectReadonlyWidget, ManyToManyReadonlyWidget, ReadonlyWidget

    if isinstance(field.rel, ManyToManyRel):
        return ManyToManyReadonlyWidget
    elif isinstance(field, ForeignKey):
        return ModelObjectReadonlyWidget
    else:
        return ReadonlyWidget


def get_field_from_cls_or_inst_or_none(cls_or_inst, field_name):
    try:
        return cls_or_inst._meta.get_field_by_name(field_name)[0]
    except (FieldDoesNotExist, AttributeError):
        return None


def get_cls_or_inst_model_field_data(field, field_name, cls_or_inst, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    label = field.verbose_name
    widget = ReadonlyWidget
    if not isinstance(cls_or_inst, type):
        humanized_value = field_humanized_value(cls_or_inst, field)
        display_value = field_display_value(cls_or_inst, field)
        if display_value is None:
            value_or_callable = getattr(cls_or_inst, field_name)
            value = field_value(cls_or_inst, field, value_or_callable, fun_kwargs)
        else:
            value = display_value
        if humanized_value:
            value = ReadonlyValue(value, humanized_value)
            widget = field_widget(cls_or_inst, field)
        return value, label, widget
    else:
        return None, label, widget


def get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    label = get_class_method(cls_or_inst, field_name).short_description
    if not isinstance(cls_or_inst, type):
        value_or_callable = getattr(cls_or_inst, field_name)
        return get_callable_value_or_value(value_or_callable, fun_kwargs), label, ReadonlyWidget
    else:
        return None, label, ReadonlyWidget


def get_cls_or_inst_readonly_data(field_name, cls_or_inst, fun_kwargs):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        next_cls_or_inst = getattr(cls_or_inst, current_field_name)
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, current_field_name)
        if field and hasattr(field, 'rel'):
            next_cls_or_inst = next_cls_or_inst or field.rel.to
        return get_cls_or_inst_readonly_data(next_field_name, next_cls_or_inst, fun_kwargs)
    else:
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, field_name)
        if field:
            return get_cls_or_inst_model_field_data(field, field_name, cls_or_inst, fun_kwargs)
        else:
            return get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs)


def get_readonly_field_data(field_name, instances, fun_kwargs, request):
    for inst in instances:
        try:
            return get_cls_or_inst_readonly_data(field_name, inst, fun_kwargs)
        except AttributeError:
            pass

    raise AttributeError('Field or method with name %s not found' % field_name)


def display_for_value(value):
    from django.contrib.admin.util import display_for_value as admin_display_for_value

    if isinstance(value, bool):
        value = _('Yes') if value else _('No')
    else:
        value = admin_display_for_value(value)
    return value


def get_obj_url(request, obj):
    if (hasattr(getattr(obj, 'get_absolute_url', None), '__call__')
        and hasattr(getattr(obj, 'can_see_edit_link', None), '__call__')
            and obj.can_see_edit_link(request)):
        return obj.get_absolute_url()
    else:
        from is_core.site import get_model_core
        model_core = get_model_core(obj.__class__)

        if model_core and hasattr(model_core, 'ui_patterns'):
            edit_pattern = model_core.ui_patterns.get('edit')
            if edit_pattern and edit_pattern.can_call_get(request, obj=obj):
                return edit_pattern.get_url_string(request, obj=obj)
    return None


def render_model_object_with_link(request, obj, display_value=None):
    obj_url = get_obj_url(request, obj)
    display_value = display_value or force_text(obj)
    return format_html('<a href="{}">{}</a>', obj_url, display_value) if obj_url else display_value
