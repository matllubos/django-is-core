import os

from distutils.version import StrictVersion

from itertools import chain

import django
from django import forms
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join, conditional_escape
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.files import FieldFile
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Widget, MultiWidget, TextInput
from django.forms.utils import flatatt
from django.core.validators import EMPTY_VALUES
from django.db.models.base import Model

try:
    from sorl.thumbnail import default
except ImportError:
    default = None

from is_core.config import settings
from is_core.utils.compatibility import CompatibilityWidgetMixin

from .utils import ReadonlyValue, add_class_name


EMPTY_VALUE = '---'


def flat_data_attrs(attrs):
    return format_html_join('', ' data-{0}="{1}"', sorted(attrs.items()))


class WrapperWidget(forms.Widget):

    def __init__(self, widget):
        self.widget = widget

    @property
    def media(self):
        return self.widget.media

    @property
    def attrs(self):
        return self.widget.attrs

    def build_attrs(self, *args, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(*args, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)

    def render(self, name, value, attrs=None):
        return self.widget.render(name, value, attrs)


class FulltextSelect(forms.Select):

    class_name = 'fulltext-search'
    placeholder = _('Search...')


class FulltextSelectMultiple(forms.SelectMultiple):

    class_name = 'fulltext-search-multiple'
    placeholder = _('Search...')


class ClearableFileInput(forms.ClearableFileInput):

    def render(self, name, value, attrs=None):
        if StrictVersion(django.get_version()) >= StrictVersion('1.8'):
            return super(ClearableFileInput, self).render(name, value, attrs)
        else:
            substitutions = {
                'initial_text': self.initial_text,
                'input_text': self.input_text,
                'clear_template': '',
                'clear_checkbox_label': self.clear_checkbox_label,
            }
            template = '%(input)s'
            substitutions['input'] = super(forms.ClearableFileInput, self).render(name, value, attrs)

            if value and hasattr(value, "url"):
                template = self.template_with_initial
                substitutions['initial'] = format_html(self.url_markup_template,
                                                       value.url,
                                                       os.path.basename(force_text(value)))
                if not self.is_required:
                    checkbox_name = self.clear_checkbox_name(name)
                    checkbox_id = self.clear_checkbox_id(checkbox_name)
                    substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                    substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                    substitutions['clear'] = forms.CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                    substitutions['clear_template'] = self.template_with_clear % substitutions

            return mark_safe(template % substitutions)

    def get_template_substitution_values(self, value):
        """
        Return value-related substitutions.
        """
        return {
            'initial': os.path.basename(conditional_escape(value)),
            'initial_url': conditional_escape(value.url),
        }


class DragAndDropFileInput(ClearableFileInput):

    def _render_value(self, value):
        return '<a href="%s">%s</a>' % (value.url, os.path.basename(value.name))

    def render(self, name, value, attrs={}):
        output = ['<div class="drag-and-drop-wrapper">']
        output.append('<div class="drag-and-drop-placeholder"%s></div>' % (id and 'data-for="%s"' % id or ''))
        output.append('<div class="thumbnail-wrapper">')
        if value and isinstance(value, FieldFile):
            output.append(self._render_value(value))
        output.append('</div><div class=file-input-wrapper>')
        output.append(super(DragAndDropFileInput, self).render(name, value, attrs=attrs))
        output.append(2 * '</div>')
        return mark_safe('\n'.join(output))


class DragAndDropImageInput(DragAndDropFileInput):

    def _get_thumbnail(self, value):
        if not default:
            raise ImproperlyConfigured('Please install sorl.thumbnail before using drag-and-drop file input')
        return default.backend.get_thumbnail(value, '64x64', crop='center')

    def _render_value(self, value):
        thumbnail = self._get_thumbnail(value)
        return '<img src="%s" alt="%s">' % (thumbnail.url, thumbnail.name)


class SmartWidgetMixin:

    def smart_render(self, request, name, value, initial_value, form, *args, **kwargs):
        return self.render(name, value, *args, **kwargs)


class ReadonlyWidget(SmartWidgetMixin, Widget):

    def __init__(self, widget=None, attrs=None):
        super(ReadonlyWidget, self).__init__(attrs)
        self.widget = widget

    def _get_widget(self):
        widget = self.widget
        while isinstance(widget, WrapperWidget):
            widget = widget.widget
        return widget

    def _get_value(self, value):
        widget = self._get_widget()
        return dict(self.widget.choices).get(value, value) if widget and hasattr(widget, 'choices') else value

    def _get_value_display(self, value):
        from is_core.utils import display_for_value

        value = self._get_value(value)

        if value in EMPTY_VALUES:
            value = EMPTY_VALUE

        return display_for_value(value)

    def _render(self, name, value, attrs=None, choices=()):
        if isinstance(value, (list, tuple)):
            out = ', '.join([self._get_value_display(val) for val in value])
        else:
            out = self._get_value_display(value)
        return mark_safe('<p>{}</p>'.format(conditional_escape(out)))

    def _smart_render(self, request, name, value, initial_value, form, attrs=None, choices=()):
        return self._render(name, value, attrs, choices)

    def _render_readonly_value(self, readonly_value):
        return mark_safe('<p><span title="%s">%s</span></p>' % (conditional_escape(force_text(readonly_value.value)),
                                                                conditional_escape(readonly_value.humanized_value)))

    def render(self, name, value, attrs=None, choices=()):
        if isinstance(value, ReadonlyValue):
            return self._render_readonly_value(value)
        else:
            return self._render(name, value, attrs, choices)

    def smart_render(self, request, name, value, initial_value, form, attrs=None, choices=()):
        return (
            self._render_readonly_value(value) if isinstance(value, ReadonlyValue)
            else self._smart_render(request, name, value, initial_value, form, attrs, choices)
        )

    def _has_changed(self, initial, data):
        return False


class ModelObjectReadonlyWidget(ReadonlyWidget):

    def _render_object(self, request, obj, display_value=None):
        from is_core.utils import render_model_object_with_link

        return render_model_object_with_link(request, obj, display_value)

    def _smart_render(self, request, name, value, initial_value, form, *args, **kwargs):
        if value and isinstance(value, Model):
            return mark_safe('<p>%s</p>' % self._render_object(request, value))
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(request, name, value, initial_value, form,
                                                                        *args, **kwargs)


class NullBooleanReadonlyWidget(ReadonlyWidget):

    def _get_value(self, value):
        return {
            '2': True,
            True: True,
            'True': True,
            '3': False,
            'False': False,
            False: False,
        }.get(value)


class ManyToManyReadonlyWidget(ModelObjectReadonlyWidget):

    def _smart_render(self, request, name, value, initial_value, form, *args, **kwargs):
        if value and isinstance(value, (list, tuple)):
            return mark_safe(', '.join((self._render_object(request, obj) for obj in value)))
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(request, name, value, initial_value, form,
                                                                        *args, **kwargs)


class ModelChoiceReadonlyWidget(ModelObjectReadonlyWidget):

    def _choice(self, value):
        widget = self._get_widget()
        if hasattr(widget, 'choices'):
            return widget.choices.get_choice_from_value(value)

    def _smart_render(self, request, name, value, initial_value, form, attrs=None, choices=()):
        choice = self._choice(value)

        out = []
        if choice:
            value = self._render_object(request, choice.obj, force_text(choice[1]))

        else:
            if value in EMPTY_VALUES:
                value = EMPTY_VALUE

        out.append(value)
        return mark_safe('<p>%s</p>' % '\n'.join(out))


class ModelMultipleReadonlyWidget(ModelChoiceReadonlyWidget):

    def _smart_render(self, request, name, values, initial_values, form, *args, **kwargs):
        if values and isinstance(values, (list, tuple)):
            rendered_values = []
            for value in values:
                choice = self._choice(value)
                if choice:
                    value = force_text(choice[1])
                    if choice.obj:
                        rendered_values.append(self._render_object(request, choice.obj, value))
                    else:
                        rendered_values.append(value)
            return mark_safe('<p>%s</p>' % rendered_values and ', '.join(rendered_values) or EMPTY_VALUE)
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(request, name, values, initial_values, form,
                                                                        *args, **kwargs)


class URLReadonlyWidget(ReadonlyWidget):

    def _render(self, name, value, *args, **kwargs):
        if value:
            return mark_safe('<a href="%s">%s</a>' % (value, value))
        else:
            return super(URLReadonlyWidget, self)._render(name, value, *args, **kwargs)


class FileReadonlyWidget(ReadonlyWidget):

    def _render(self, name, value, *args, **kwargs):
        if value and isinstance(value, FieldFile):
            return mark_safe('<a href="%s">%s</a>' % (value.url, os.path.basename(value.name)))
        else:
            return super(FileReadonlyWidget, self)._render(name, value, *args, **kwargs)


class EmptyWidget(ReadonlyWidget):

    def render(self, *args, **kwargs):
        return ''

    def smart_render(self, *args, **kwargs):
        return ''


class ButtonWidget(CompatibilityWidgetMixin, ReadonlyWidget):

    def _render(self, name, value, attrs=None, *args, **kwargs):
        final_attrs = self.build_attrs(self.attrs, attrs, name=name)

        return format_html('<button %(attrs)s>%(value)s</button>' %
                           {'value': value, 'attrs': flatatt(final_attrs)})


class DivButtonWidget(CompatibilityWidgetMixin, ReadonlyWidget):

    def _render(self, name, value, attrs=None, *args, **kwargs):
        final_attrs = self.build_attrs(self.attrs, attrs)
        class_name = final_attrs.pop('class', '')
        return format_html('<div class="%(class_name)s btn btn-primary btn-small" '
                           '%(attrs)s>%(value)s</div>' %
                           {'class_name': class_name, 'value': value, 'attrs': flatatt(final_attrs)})


class MultipleTextInput(forms.TextInput):

    def __init__(self, attrs=None, separator=','):
        super(MultipleTextInput, self).__init__(attrs)
        self.separator = separator

    def render(self, name, value, attrs=None):
        if isinstance(value, str):
            value = [value]
        return super(MultipleTextInput, self).render(
            name, '{} '.format(self.separator).join(map(force_text, value)) if value else value, attrs
        )

    def value_from_datadict(self, data, files, name):
        value = super(MultipleTextInput, self).value_from_datadict(data, files, name)
        return [v.strip() for v in value.split(self.separator)] if isinstance(value, str) else value


class AbstractDateRangeWidget(MultiWidget):

    def __init__(self):
        class_from, class_to = self.get_range_classes()
        super(AbstractDateRangeWidget, self).__init__(
            (
                TextInput(attrs={'class': class_from}),
                TextInput(attrs={'class': class_to}),
            )
        )

    def get_range_classes(self):
        raise NotImplemented

    def decompress(self, value):
        return []


class DateRangeWidget(AbstractDateRangeWidget):

    def get_range_classes(self):
        return 'date-range-from', 'date-range-to'


class DateTimeRangeWidget(AbstractDateRangeWidget):

    def get_range_classes(self):
        return 'datetime-range-from', 'datetime-range-to'


class FilterDateRangeWidgetMixin:

    def render(self, name, value, attrs=None):
        if attrs and 'data-filter' in attrs:
            filter_term = attrs.pop('data-filter')
            for widget, operator in zip(self.widgets, ('gte', 'lt')):
                widget.attrs['data-filter'] = '{}__{}'.format(filter_term.rsplit('__', 1)[0], operator)
        return super(FilterDateRangeWidgetMixin, self).render(name, value, attrs)


class DateRangeFilterWidget(FilterDateRangeWidgetMixin, DateRangeWidget):
    pass


class DateTimeRangeFilterWidget(FilterDateRangeWidgetMixin, DateTimeRangeWidget):
    pass


class RestrictedSelectWidgetMixin(CompatibilityWidgetMixin):

    select_class_name = None
    select_class_placeholder = None

    @cached_property
    def is_restricted(self):
        """
        Returns True or False according to number of objects in queryset.
        If queryset contains too much objects the widget will be restricted and won't be used select box with choices.
        """
        return (
            not hasattr(self.choices, 'queryset') or
            self.choices.queryset.count() > settings.FOREIGN_KEY_MAX_SELECBOX_ENTRIES
        )

    def render(self, name, value, attrs=None):
        if self.is_restricted:
            if value is None:
                value = ''
            final_attrs = self.build_attrs(self.attrs, attrs, type='text', name=name)
            if value != '':
                # Only add the 'value' attribute if a value is non-empty.
                final_attrs['value'] = self.format_resticted_value(value)
            return format_html('<input{} />', flatatt(final_attrs))
        else:
            attrs = add_class_name(attrs, self.select_class_name)
            attrs['placeholder'] = self.select_class_placeholder
            return super(RestrictedSelectWidgetMixin, self).render(name, value, attrs=attrs)


class RestrictedSelectWidget(RestrictedSelectWidgetMixin, forms.Select):

    select_class_name = 'fulltext-search'
    select_class_placeholder = _('Search...')

    def format_resticted_value(self, value):
        return None if value is None else str(value)


class RestrictedSelectMultipleWidget(RestrictedSelectWidgetMixin, forms.SelectMultiple):

    select_class_name = 'fulltext-search-multiple'
    select_class_placeholder = _('Search...')

    def __init__(self, attrs=None, separator=','):
        super(RestrictedSelectMultipleWidget, self).__init__(attrs)
        self.separator = separator

    def value_from_datadict(self, data, files, name):
        if self.is_restricted:
            value = data.get(name)
            return [v.strip() for v in value.split(self.separator)] if isinstance(value, str) else value
        else:
            return super(RestrictedSelectMultipleWidget, self).value_from_datadict(data, files, name)

    def format_resticted_value(self, value):
        if value is None:
            value = []
        if not isinstance(value, (tuple, list)):
            value = [value]
        return self.separator.join([str(v) if v is not None else '' for v in value])
