import re
import inspect
import types

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.contrib.admin.utils import display_for_value as admin_display_for_value
from django.db.models import Model, QuerySet
from django.db.models.fields import FieldDoesNotExist
from django.forms.forms import pretty_name
from django.utils.encoding import force_text
from django.utils.translation import ugettext
from django.utils.html import format_html, format_html_join

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
    try:
        return model._meta.get_field(field_name)
    except (FieldDoesNotExist, AttributeError):
        return None


def _get_verbose_value(raw, field_or_method, obj, **kwargs):
    if hasattr(field_or_method, 'humanized') and field_or_method.humanized:
        return field_or_method.humanized(raw, obj, **kwargs)
    elif hasattr(field_or_method, 'attname') and hasattr(obj, 'get_{}_display'.format(field_or_method.attname)):
        return getattr(obj, 'get_{}_display'.format(field_or_method.attname))()
    else:
        return raw


def _val_to_readonly_value(value, field_or_method, obj, **kwargs):
    from is_core.forms.utils import ReadonlyValue
    verbose_value = _get_verbose_value(value, field_or_method, obj, **kwargs)
    return ReadonlyValue(value, verbose_value) if value != verbose_value else value


def _get_method_value(method, field_name, inst, fun_kwargs):
    method_kwargs_names = inspect.getfullargspec(method)[0][1:]
    method_kwargs = {arg_name: fun_kwargs[arg_name]  for arg_name in method_kwargs_names if arg_name in fun_kwargs}
    if len(method_kwargs_names) == len(method_kwargs):
        return _val_to_readonly_value(method(**method_kwargs), method, inst,
                                     **{k: v for k, v in method_kwargs.items() if k != 'obj'})
    else:
        raise(InvalidMethodArguments('Method {} arguments has not subset of fun kwargs'.format(field_name)))


def _get_method_or_property_value(class_method, field_name, inst, fun_kwargs):
    method_or_property = getattr(inst, field_name)

    return (
        _get_method_value(method_or_property, field_name, inst, fun_kwargs) if is_callable(method_or_property)
        else _val_to_readonly_value(method_or_property, class_method, inst)
    )


def get_model_method_or_property_data(field_name, model, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    class_method = get_class_method(model, field_name)

    method = (
        getattr(model, field_name)
        if hasattr(model, field_name) and not class_method and is_callable(getattr(model, field_name))
        else class_method
    )

    if method:
        if hasattr(method, 'field'):
            # Generic relation
            label = getattr(method.field, 'verbose_name', pretty_name(field_name))
        else:
            label = getattr(method, 'short_description', pretty_name(field_name))
        try:
            return (
                (None, label, ReadonlyWidget) if isinstance(model, type)
                else (_get_method_or_property_value(method, field_name, model, fun_kwargs), label, ReadonlyWidget)
            )
        except InvalidMethodArguments:
            return None
    elif hasattr(model, field_name):
        return (
            getattr(model, field_name), pretty_name(field_name), ReadonlyWidget
        )
    else:
        return None


def _get_model_field_data(field, model):
    from is_core.forms.widgets import ReadonlyWidget, ManyToManyReadonlyWidget, ModelObjectReadonlyWidget

    if field.auto_created and (field.one_to_many or field.many_to_many):
        return (
             None if isinstance(model, type) else [obj for obj in getattr(model, field.name).all()], (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name_plural
            ), ManyToManyReadonlyWidget
        )
    elif field.auto_created and field.one_to_one:
        return (
            None if isinstance(model, type) or not hasattr(model, field.name)
            else getattr(model, field.name), (
                getattr(field.field, 'reverse_verbose_name', None)
                if getattr(field.field, 'reverse_verbose_name', None) is not None
                else field.related_model._meta.verbose_name
            ),  ModelObjectReadonlyWidget
        )
    elif field.many_to_many:
        return (
            None if isinstance(model, type) else [obj for obj in getattr(model, field.name).all()],
            field.verbose_name, ManyToManyReadonlyWidget
        )
    else:
        return (
            None if isinstance(model, type)
            else _val_to_readonly_value(
                getattr(model, field.name) if hasattr(model, field.name) else None, field, model
            ), getattr(field, 'verbose_name', pretty_name(field.name)), ReadonlyWidget
        )


def _get_model_readonly_data(field_name, model, fun_kwargs):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        field = get_field_from_model_or_none(model, current_field_name)
        if hasattr(model, current_field_name) and getattr(model, current_field_name):
            return _get_model_readonly_data(next_field_name, getattr(model, current_field_name), fun_kwargs)
        elif model and field and hasattr(field, 'related_model'):
            return _get_model_readonly_data(next_field_name, field.related_model, fun_kwargs)
        else:
            return None
    else:
        field = get_field_from_model_or_none(model, field_name)
        return (
            _get_model_field_data(field, model) if field
            else get_model_method_or_property_data(field_name, model, fun_kwargs)
        )


def _get_view_readonly_data(field_name, view, fun_kwargs):
    from is_core.forms.widgets import ReadonlyWidget

    method_field = view.get_method_returning_field_value(field_name)
    if method_field:
        try:
            return (
                _get_method_value(method_field, field_name, view, fun_kwargs),
                getattr(method_field, 'short_description', pretty_name(field_name)),
                ReadonlyWidget
            )
        except InvalidMethodArguments:
            return None
    else:
        return None


def get_readonly_field_data(field_name, instance, view=None, fun_kwargs=None):
    """
    Returns field humanized value, label and widget which are used to display of instance or view readonly data.
    Args:
        field_name: name of the field which will be displayed
        instance: model instance
        view: view instance
        fun_kwargs: kwargs that can be used inside method call

    Returns:
        field humanized value, label and widget which are used to display readonly data
    """
    fun_kwargs = fun_kwargs or {}

    if view:
        view_readonly_data = _get_view_readonly_data(field_name, view, fun_kwargs)
        if view_readonly_data is not None:
            return view_readonly_data

    field_data = _get_model_readonly_data(field_name, instance, fun_kwargs)
    if field_data is not None:
        return field_data

    raise FieldOrMethodDoesNotExist('Field or method with name {} not found'.format(field_name))


def display_object_data(obj, field_name, request=None):
    """
    Returns humanized value of model object that can be rendered to HTML or returned as part of REST

    examples:
       boolean True/Talse ==> Yes/No
       objects ==> object display name with link if current user has permissions to see the object
       field with choices ==> string value of choice
       field with humanize function ==> result of humanize function
    """
    from is_core.forms.utils import ReadonlyValue

    value, _, _ = get_readonly_field_data(field_name, obj)
    return display_for_value(value.humanized_value if isinstance(value, ReadonlyValue) else value, request=request)


def display_for_value(value, request=None):
    """
    Converts humanized value

    examples:
        boolean True/Talse ==> Yes/No
        objects ==> object display name with link if current user has permissions to see the object
        datetime ==> in localized format
        list ==> values separated with ","
        dict ==> string formatted with HTML ul/li tags
    """

    if request and isinstance(value, Model):
        return render_model_object_with_link(request, value)
    elif isinstance(value, (QuerySet, list, tuple, set, types.GeneratorType)):
        return format_html_join(
            ', ',
            '{}',
            (
                (display_for_value(v, request),) for v in value
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
        return admin_display_for_value(value, '-')


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
        return call_method_with_unknown_input(obj.get_absolute_url, request=request)
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

    def get_method_returning_field_value(self, field_name):
        """
        Method should return object method that can be used to get field value.
        Args:
            field_name: name of the field

        Returns: method for obtaining a field value

        """
        method = getattr(self, field_name, None)
        return method if method and callable(method) else None


def get_model_name(model):
    return str(model._meta.model_name)
