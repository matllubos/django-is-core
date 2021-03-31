import re
import json
import inspect
import types

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.contrib.admin.utils import display_for_value as admin_display_for_value
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, QuerySet
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import pretty_name
from django.utils.encoding import force_text
from django.utils.translation import ugettext
from django.utils.html import format_html, format_html_join

from chamber.utils import call_function_with_unknown_input

from pyston.converters import get_converter
from pyston.serializer import get_resource_class_or_none


PK_PATTERN = r'(?P<pk>[^/]+)'
NUMBER_PK_PATTERN = '(?P<pk>\d+)'

EMPTY_VALUE = '---'

LOOKUP_SEP = '__'


def is_callable(val):
    return hasattr(val, '__call__')


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
        elif 'inline_view_inst' in opts:
            inline_views.append(opts.get('inline_view_inst'))
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


def get_field_from_model_or_none(model, field_name):
    """
    Return field from model. If field doesn't exists null is returned instead of exception.
    """
    try:
        return model._meta.get_field(field_name)
    except (FieldDoesNotExist, AttributeError):
        return None


def get_field_label_from_path(model, field_path, view=None, field_labels=None):
    """
    Return field label of model class for input field path. For every field name in the field path is firstly get the
    right label and these labels are joined with " - " separator to one string.

    field_label input parameter can affect the result value. Example:

    * field_path='user__email', field_labels={} => 'user email'  # default values get from fields
    * field_path='user__email', field_labels={'user__email': 'e-mail'} => 'e-mail'  # full value is replaced
    * field_path='user__email', field_labels={'user': 'customer'} => 'customer - email'  # related field prefix is changed
    * field_path='user', field_labels={'user': 'customer'} => 'customer'  # full value is replaced
    * field_path='user', field_labels={'user__': 'customer'} => 'user'  # has no effect
    * field_path='user__email', field_labels={'user__': 'customer'} => 'customer email'  # related field prefix is changed
    * field_path='user__email', field_labels={'user__': None} => 'email'  # related field prefix is ignored
    * field_path='user__email', field_labels={'email': 'e-mail'} => 'user email'  # has no effect

    :param model: Django model class
    :param field_path: field names separated with "__"
    :param view: view instance
    :param field_labels: dict of field labels which can override result field name
    :return: field label
    """
    from .field_api import get_field_descriptors_from_path

    field_labels = {} if field_labels is None else field_labels

    field_descriptors = get_field_descriptors_from_path(model, field_path, view)

    used_field_names = []
    field_descriptor_labels = []

    for field_descriptor in field_descriptors:
        field_path_prefix = LOOKUP_SEP.join(used_field_names)
        current_field_path = LOOKUP_SEP.join(used_field_names + [field_descriptor.field_name])

        if field_descriptor_labels and field_path_prefix + LOOKUP_SEP in field_labels:
            if field_labels[field_path_prefix + LOOKUP_SEP] is not None:
                field_descriptor_labels = [field_labels[field_path_prefix + LOOKUP_SEP]]
            else:
                field_descriptor_labels = []

        if current_field_path in field_labels:
            if field_labels[current_field_path] is not None:
                field_descriptor_labels = [field_labels[current_field_path]]
            else:
                field_descriptor_labels = []
        elif field_descriptor.field_name != '_obj_name' or not field_descriptor_labels:
            if field_descriptor.get_label() is not None:
                field_descriptor_labels.append(field_descriptor.get_label())

        used_field_names.append(field_descriptor.field_name)

    return ' - '.join([str(label) for label in field_descriptor_labels if label is not None])


def get_field_widget_from_path(model, field_path, view=None):
    """
    Return form widget to show value get from model instance and field_path
    """
    from .field_api import get_field_descriptors_from_path

    return get_field_descriptors_from_path(model, field_path, view)[-1].get_widget()


def get_readonly_field_value_from_path(instance, field_path, request=None, view=None):
    """
    Return ReadonlyValue instance which contains value and humanized value get from model instance and field_path
    """

    from .field_api import get_field_value_from_path

    return get_field_value_from_path(instance, field_path, request, view, return_readonly_value=True)


def get_readonly_field_data(instance, field_name, request, view=None, field_labels=None):
    """
    Returns field humanized value, label and widget which are used to display of instance or view readonly data.
    Args:
        field_name: name of the field which will be displayed
        instance: model instance
        view: view instance
        field_labels: dict of field labels which rewrites the generated field label

    Returns:
        field humanized value, label and widget which are used to display readonly data
    """
    return (
        get_readonly_field_value_from_path(instance, field_name, request, view),
        get_field_label_from_path(instance.__class__, field_name, view, field_labels),
        get_field_widget_from_path(instance.__class__, field_name, view)
    )


def display_object_data(obj, field_name, request, view=None):
    """
    Returns humanized value of model object that can be rendered to HTML or returned as part of REST

    examples:
       boolean True/False ==> Yes/No
       objects ==> object display name with link if current user has permissions to see the object
       field with choices ==> string value of choice
       field with humanize function ==> result of humanize function
    """
    return display_for_value(get_readonly_field_value_from_path(obj, field_name, request, view), request=request)


def display_code(value):
    """
    Display input value as a code.
    """
    return format_html(
        '<pre>{}</pre>',
        value
    ) if value else display_for_value(value)


def display_json(value):
    """
    Display input JSON as a code
    """
    if value is None:
        return display_for_value(value)
    if isinstance(value, str):
        value = json.loads(value)
    return display_code(json.dumps(value, indent=2, ensure_ascii=False, cls=DjangoJSONEncoder))


def display_for_value(value, request=None):
    """
    Converts humanized value

    examples:
        boolean True/False ==> Yes/No
        objects ==> object display name with link if current user has permissions to see the object
        datetime ==> in localized format
        list ==> values separated with ","
        dict ==> string formatted with HTML ul/li tags
    """
    from is_core.forms.utils import ReadonlyValue

    if isinstance(value, ReadonlyValue):
        value = value.value

    if request and isinstance(value, Model):
        return render_model_object_with_link(request, value)
    elif isinstance(value, (QuerySet, list, tuple, set, types.GeneratorType)):
        return format_html(
            '<ol class="field-list">{}</ol>',
            format_html_join(
                '\n',
                '<li>{}</li>',
                (
                    (display_for_value(v, request),) for v in value
                )
            )
        )
    elif isinstance(value, dict):
        return format_html(
            '<ul class="field-dict">{}</ul>',
            format_html_join(
                '\n',
                '{}{}',
                (
                    (
                        format_html('<li>{}</li>', k),
                        (
                            display_for_value(v, request) if isinstance(v, dict)
                            else format_html(
                                '<ul class="field-dict"><li>{}</li></ul>',
                                display_for_value(v, request)
                            )
                        )
                    )
                    for k, v in value.items()
                )
            )
        )
    elif isinstance(value, bool):
        return ugettext('Yes') if value else ugettext('No')
    else:
        return admin_display_for_value(value, EMPTY_VALUE)


def get_url_from_model_core(request, obj):
    """
    Returns object URL from model core.
    """
    from is_core.site import get_model_core
    model_core = get_model_core(obj.__class__)

    if model_core and hasattr(model_core, 'ui_patterns'):
        edit_pattern = model_core.ui_patterns.get('detail')
        return (
            edit_pattern.get_url_string(request, obj=obj)
            if edit_pattern and edit_pattern.has_permission('get', request, obj=obj) else None
        )
    else:
        return None


def get_obj_url(request, obj):
    """
    Returns object URL if current logged user has permissions to see the object
    """
    if (is_callable(getattr(obj, 'get_absolute_url', None)) and
            (not hasattr(obj, 'can_see_edit_link') or
             (is_callable(getattr(obj, 'can_see_edit_link', None)) and obj.can_see_edit_link(request)))):
        return call_function_with_unknown_input(obj.get_absolute_url, request=request)
    else:
        return get_url_from_model_core(request, obj)


def render_model_object_with_link(request, obj, display_value=None):
    if obj is None:
        return '[{}]'.format(ugettext('missing object'))

    obj_url = get_obj_url(request, obj)
    display_value = str(obj) if display_value is None else str(display_value)

    return format_html('<a href="{}">{}</a>', obj_url, display_value) if obj_url else display_value


def render_model_objects_with_link(request, objs):
    return format_html_join(', ', '{}', ((render_model_object_with_link(request, obj),) for obj in objs))


def header_name_to_django(header_name):
    return '_'.join(('HTTP', header_name.replace('-', '_').upper()))


def pretty_class_name(class_name):
    return re.sub(r'(\w)([A-Z])', r'\1-\2', class_name).lower()


def get_export_types_with_content_type(export_types):
    generated_export_types = []
    for title, type, serialization_format in export_types:
        try:
            generated_export_types.append(
                (title, type, serialization_format, get_converter(type).media_type)
            )
        except KeyError:
            raise ImproperlyConfigured('Missing converter for type {}'.format(type))
    return generated_export_types


def get_link_or_none(pattern_name, request, view_kwargs=None):
    """
    Helper that generate URL prom pattern name and kwargs and check if current request has permission to open the URL.
    If not None is returned.

    Args:
        pattern_name (str): slug which is used for view registratin to pattern
        request (django.http.request.HttpRequest): Django request object
        view_kwargs (dict): list of kwargs necessary for URL generator

    Returns:

    """
    from is_core.patterns import reverse_pattern

    pattern = reverse_pattern(pattern_name)
    assert pattern is not None, 'Invalid pattern name {}'.format(pattern_name)

    if pattern.has_permission('get', request, view_kwargs=view_kwargs):
        return pattern.get_url_string(request, view_kwargs=view_kwargs)
    else:
        return None


class GetMethodFieldMixin:

    @classmethod
    def get_method_returning_field_value(cls, field_name):
        """
        Method should return object method that can be used to get field value.
        Args:
            field_name: name of the field

        Returns: method for obtaining a field value

        """
        method = getattr(cls, field_name, None)
        return method if method and callable(method) else None


def get_model_name(model):
    return str(model._meta.model_name)
