import re
import sys
import types
import inspect

from django.http.request import QueryDict
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks, conditional_escape
from django.db.models.fields.related import ManyToManyRel, ForeignKey


def str_to_class(class_string):
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), class_name)
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
        for field in opts.get('fields', ()):
            if isinstance(field, (list, tuple)):
                field_names.extend(field)
            else:
                field_names.append(field)
    return field_names


def get_callable_value(callable_value, fun_kwargs):
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


def display_for_field_value(instance, field, value, callable_value, request):
    if (isinstance(field.rel, ManyToManyRel) and callable_value is not None and
        hasattr(getattr(callable_value, 'all'), '__call__')):
        return mark_safe('<ul>%s</ul>' % ''.join(['<li>%s</li>' % force_text(obj) for obj in callable_value.all()]))

    elif (isinstance(field, ForeignKey)
          and hasattr(getattr(callable_value, 'get_absolute_url', None), '__call__')
          and hasattr(getattr(callable_value, 'can_see_edit_link', None), '__call__')
          and callable_value.can_see_edit_link(request)):
        return mark_safe('<a href="%s">%s</a>' % (callable_value.get_absolute_url(), force_text(value)))

    elif hasattr(instance, field.name):
        humanize_method_name = 'get_%s_humanized' % field.name
        if hasattr(getattr(instance, humanize_method_name, None), '__call__'):
            return mark_safe('<span title="%s">%s</span>' % (force_text(value), getattr(instance,
                                                                                        humanize_method_name)()))
    return value


def get_instance_field_value_and_label(field_name, instance, fun_kwargs, request):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        return get_instance_field_value_and_label(next_field_name, getattr(instance, current_field_name), fun_kwargs,
                                                  request)
    else:
        callable_value = getattr(instance, 'get_%s_display' % field_name, None)
        if not callable_value:
            # Exeption because OneToOne Field
            try:
                callable_value = getattr(instance, field_name)
            except ObjectDoesNotExist:
                callable_value = None
        value = get_callable_value(callable_value, fun_kwargs)

        value = display_for_value(value)

        try:
            field = instance._meta.get_field_by_name(field_name)[0]
        except (FieldDoesNotExist, AttributeError):
            field = None

        if field:
            label = field.verbose_name

            value = display_for_field_value(instance, field, value, callable_value, request)

        else:
            label = callable_value.short_description

        return mark_safe(linebreaks(conditional_escape(force_text(value)))), label


def get_field_value_and_label(field_name, instances, fun_kwargs, request):
    for inst in instances:
        try:
            return get_instance_field_value_and_label(field_name, inst, fun_kwargs, request)
        except AttributeError:
            pass
    raise AttributeError('Field with name %s not found' % field_name)


def display_for_value(value):
    from django.contrib.admin.util import display_for_value as admin_display_for_value

    if isinstance(value, bool):
        value = _('Yes') if value else _('No')
    else:
        value = admin_display_for_value(value)
    return value

