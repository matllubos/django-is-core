from __future__ import unicode_literals

import re
import sys
import types
import inspect

import django
from django.http.request import QueryDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks, conditional_escape
from django.db.models.fields.related import ManyToManyRel, ForeignKey
from django.db.models.base import Model

from chamber.utils import get_class_method

from is_core.utils.compatibility import get_field_from_model


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
    for _, opts in fieldsets or ():
        if 'fieldsets' in opts:
            field_names += flatten_fieldsets(opts.get('fieldsets'))
        else:
            for field in opts.get('fields', ()):
                if isinstance(field, (list, tuple)):
                    field_names.extend(field)
                else:
                    field_names.append(field)
    return field_names


def get_inline_views_from_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    inline_views = []
    for _, opts in fieldsets or ():
        if 'fieldsets' in opts:
            inline_views += get_inline_views_from_fieldsets(opts.get('fieldsets'))
        elif 'inline_view' in opts:
            inline_views.append(opts.get('inline_view'))
    return inline_views


def get_inline_views_opts_from_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    inline_views = []
    for _, opts in fieldsets or ():
        if 'fieldsets' in opts:
            inline_views += get_inline_views_opts_from_fieldsets(opts.get('fieldsets'))
        elif 'inline_view' in opts:
            inline_views.append(opts)
    return inline_views


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
    return (
        getattr(instance, humanize_method_name)() if hasattr(getattr(instance, humanize_method_name, None), '__call__')
        else None
    )


def field_display_value(instance, field):
    display_method_name = 'get_%s_display' % field.name
    return (
        getattr(instance, display_method_name)() if hasattr(getattr(instance, display_method_name, None), '__call__')
        else None
    )


def field_value(instance, field, value, fun_kwargs):
    if field.many_to_many or field.one_to_many and value is not None and hasattr(getattr(value, 'all'), '__call__'):
        return [obj for obj in value.all()]
    elif field.one_to_one or field.many_to_one:
        return value
    else:
        return get_callable_value_or_value(value, fun_kwargs)


def get_field_from_cls_or_inst_or_none(cls_or_inst, field_name):
    from django.db.models.fields import FieldDoesNotExist

    try:
        return get_field_from_model(cls_or_inst, field_name)
    except (FieldDoesNotExist, AttributeError):
        return None


def get_widget_and_label_from_fiel(field):
    from is_core.forms.widgets import ReadonlyWidget, ManyToManyReadonlyWidget, ModelObjectReadonlyWidget

    if field.auto_created and (field.one_to_many or field.many_to_many):
        return (
            (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name_plural
            ), ManyToManyReadonlyWidget
        )
    elif field.auto_created and field.one_to_one:
        return (
            (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name_plural
            ),  ModelObjectReadonlyWidget
        )
    else:
        return (field.verbose_name, ReadonlyWidget)


def get_cls_or_inst_model_field_data(field, field_name, cls_or_inst, fun_kwargs):
    from is_core.forms.forms import ReadonlyValue

    label, widget = get_widget_and_label_from_fiel(field)

    if not isinstance(cls_or_inst, type):
        display_value = field_display_value(cls_or_inst, field)
        value = (
            field_value(cls_or_inst, field, getattr(cls_or_inst, field_name), fun_kwargs) if display_value is None
            else display_value
        )
        humanized_value = field_humanized_value(cls_or_inst, field)
        return (ReadonlyValue(value, humanized_value) if humanized_value else value, label, widget)
    else:
        return (None, label, widget)


def get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    label = get_class_method(cls_or_inst, field_name).short_description
    return (
        (None, label, ReadonlyWidget) if isinstance(cls_or_inst, type)
        else (get_callable_value_or_value(getattr(cls_or_inst, field_name), fun_kwargs), label, ReadonlyWidget)
    )


def get_cls_or_inst_readonly_data(field_name, cls_or_inst, fun_kwargs):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, current_field_name)
        next_cls_or_inst = (
            field.rel.to if field and hasattr(field, 'rel') and not hasattr(cls_or_inst, current_field_name)
            else getattr(cls_or_inst, current_field_name)
        )
        return get_cls_or_inst_readonly_data(next_field_name, next_cls_or_inst, fun_kwargs)
    else:
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, field_name)
        return (
            get_cls_or_inst_model_field_data(field, field_name, cls_or_inst, fun_kwargs) if field
            else get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs)
        )


def get_readonly_field_data(field_name, instances, fun_kwargs, request):
    for inst in instances:
        try:
            return get_cls_or_inst_readonly_data(field_name, inst, fun_kwargs)
        except AttributeError:
            pass

    raise AttributeError('Field or method with name %s not found' % field_name)


def display_for_value(value):
    if isinstance(value, bool):
        return ugettext('Yes') if value else ugettext('No')
    else:
        from is_core.utils.compatibility import admin_display_for_value

        return admin_display_for_value(value)


def get_obj_url(request, obj):
    if (hasattr(getattr(obj, 'get_absolute_url', None), '__call__') and
            hasattr(getattr(obj, 'can_see_edit_link', None), '__call__') and
            obj.can_see_edit_link(request)):
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
    display_value = force_text(obj) if display_value is None else display_value
    return format_html('<a href="{}">{}</a>', obj_url, display_value) if obj_url else display_value


def header_name_to_django(header_name):
    return '_'.join(('HTTP', header_name.replace('-', '_').upper()))
