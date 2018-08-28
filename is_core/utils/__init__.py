import re
import inspect

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.forms.forms import pretty_name
from django.utils.encoding import force_text
from django.utils.translation import ugettext
from django.utils.html import format_html

from chamber.utils import get_class_method, call_method_with_unknown_input

from pyston.converters import get_converter


def is_callable(val):
    return hasattr(val, '__call__')


class FieldOrMethodDoesNotExist(Exception):
    pass


class InvalidMethodArguments(Exception):
    pass


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


def get_field_from_cls_or_inst_or_none(cls_or_inst, field_name):
    from django.db.models.fields import FieldDoesNotExist

    try:
        return cls_or_inst._meta.get_field(field_name)
    except (FieldDoesNotExist, AttributeError):
        return None


def get_verbose_value(raw, field_or_method, obj, **kwargs):
    if hasattr(field_or_method, 'humanized') and field_or_method.humanized:
        return field_or_method.humanized(raw, obj, **kwargs)
    elif hasattr(field_or_method, 'choices') and field_or_method.choices:
        return getattr(obj, 'get_{}_display'.format(field_or_method.attname))()
    else:
        return raw


def val_to_readonly_value(value, field_or_method, obj, **kwargs):
    from is_core.forms.utils import ReadonlyValue

    verbose_value = get_verbose_value(value, field_or_method, obj, **kwargs)
    return ReadonlyValue(value, verbose_value) if value != verbose_value else value


def get_callable_value(method, field_name, inst, fun_kwargs):
    callable = getattr(inst, field_name)
    method_kwargs_names = inspect.getargspec(callable)[0][1:]
    method_kwargs = {arg_name: fun_kwargs[arg_name]  for arg_name in method_kwargs_names if arg_name in fun_kwargs}
    if len(method_kwargs_names) == len(method_kwargs):
        return val_to_readonly_value(callable(**method_kwargs), method, inst,
                                     **{k: v for k, v in method_kwargs.items() if k != 'obj'})
    else:
        raise(InvalidMethodArguments('Method {} arguments has not subset of fun kwargs'.format(field_name)))


def get_callable_value_or_value(method, field_name, inst, fun_kwargs):
    return (
        get_callable_value(method, field_name, inst, fun_kwargs) if is_callable(getattr(inst, field_name))
        else val_to_readonly_value(getattr(inst, field_name), method, inst)
    )


def get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    class_method = get_class_method(cls_or_inst, field_name)

    method = (
        getattr(cls_or_inst, field_name)
        if hasattr(cls_or_inst, field_name) and not class_method and is_callable(getattr(cls_or_inst, field_name))
        else class_method
    )

    if method:
        label = getattr(method, 'short_description', pretty_name(field_name))
        try:
            return (
                (None, label, ReadonlyWidget) if isinstance(cls_or_inst, type)
                else (get_callable_value_or_value(method, field_name, cls_or_inst, fun_kwargs), label, ReadonlyWidget)
            )
        except InvalidMethodArguments:
            return None
    elif hasattr(cls_or_inst, field_name):
        return (getattr(cls_or_inst, field_name), pretty_name(field_name), ReadonlyWidget)
    else:
        return None


def get_cls_or_inst_model_field_data(field, cls_or_inst):
    from is_core.forms.widgets import ReadonlyWidget, ManyToManyReadonlyWidget, ModelObjectReadonlyWidget

    if field.auto_created and (field.one_to_many or field.many_to_many):
        return (
             None if isinstance(cls_or_inst, type) else [obj for obj in getattr(cls_or_inst, field.name).all()], (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name_plural
            ), ManyToManyReadonlyWidget
        )
    elif field.auto_created and field.one_to_one:
        return (
            None if isinstance(cls_or_inst, type) or not hasattr(cls_or_inst, field.name)
            else getattr(cls_or_inst, field.name), (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name
            ),  ModelObjectReadonlyWidget
        )
    elif field.many_to_many:
        return (
            None if isinstance(cls_or_inst, type) else [obj for obj in getattr(cls_or_inst, field.name).all()],
            field.verbose_name, ManyToManyReadonlyWidget
        )
    else:
        return (
            None if isinstance(cls_or_inst, type)
            else val_to_readonly_value(
                getattr(cls_or_inst, field.name) if hasattr(cls_or_inst, field.name) else None, field, cls_or_inst
            ), field.verbose_name, ReadonlyWidget
        )


def get_cls_or_inst_readonly_data(field_name, cls_or_inst, fun_kwargs):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, current_field_name)
        if hasattr(cls_or_inst, current_field_name):
            return get_cls_or_inst_readonly_data(next_field_name, getattr(cls_or_inst, current_field_name), fun_kwargs)
        elif field and hasattr(field, 'rel'):
            return get_cls_or_inst_readonly_data(next_field_name, field.related_model, fun_kwargs)
        else:
            return None
    else:
        field = get_field_from_cls_or_inst_or_none(cls_or_inst, field_name)
        return (
            get_cls_or_inst_model_field_data(field, cls_or_inst) if field
            else get_cls_or_inst_method_or_property_data(field_name, cls_or_inst, fun_kwargs)
        )


def get_readonly_field_data(field_name, instances, fun_kwargs):
    for inst in instances:
        data = get_cls_or_inst_readonly_data(field_name, inst, fun_kwargs)
        if data is not None:
            return data

    raise FieldOrMethodDoesNotExist('Field or method with name {} not found'.format(field_name))


def display_object_data(obj, field_name, request=None):
    """
    Returns humanized value of model object that can be rendered to HTML or returned as part of REST

    examples:
       boolean True/Talse ==> Yes/No
       objects ==> object display name with link if current user has permissions to see the object
       field with choices ==> string value of choice
       field with hummanize function ==> result of humanize function
    """
    from is_core.forms.utils import ReadonlyValue

    value, _, _ = get_readonly_field_data(field_name, [obj], {})
    return display_for_value(value.humanized_value if isinstance(value, ReadonlyValue) else value, request=request)


def display_for_value(value, request=None):
    """
    Converts humanized value

    examples:
        boolean True/Talse ==> Yes/No
        objects ==> object display name with link if current user has permissions to see the object
        datetime ==> in localized format
    """
    from is_core.utils.compatibility import admin_display_for_value

    if request and isinstance(value, Model):
        return render_model_object_with_link(request, value)
    else:
        return (
            (value and ugettext('Yes') or ugettext('No')) if isinstance(value, bool) else admin_display_for_value(value)
        )


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
            if edit_pattern and edit_pattern.can_call_get(request, obj=obj) else None
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
        return call_method_with_unknown_input(obj.get_absolute_url, request=request)
    else:
        return get_url_from_model_core(request, obj)


def render_model_object_with_link(request, obj, display_value=None):
    obj_url = get_obj_url(request, obj)
    display_value = force_text(obj) if display_value is None else display_value
    return format_html('<a href="{}">{}</a>', obj_url, display_value) if obj_url else display_value


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
