import os
from itertools import chain

import django
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import EMPTY_VALUES
from django.db.models.base import Model
from django.db.models.fields.files import FieldFile
from django.forms.utils import flatatt
from django.forms.widgets import MultiWidget, TextInput, Widget
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.html import conditional_escape, format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from is_core.config import settings
from is_core.utils import EMPTY_VALUE, display_json

from .utils import ReadonlyValue, add_class_name


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
        """Helper function for building an attribute dictionary."""
        self.attrs = self.widget.build_attrs(*args, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)

    def render(self, name, value, attrs=None, renderer=None):
        return self.widget.render(name, value, attrs, renderer)


class FulltextSelect(forms.Select):

    class_name = 'fulltext-search'
    placeholder = _('Search...')


class FulltextSelectMultiple(forms.SelectMultiple):

    class_name = 'fulltext-search-multiple'
    placeholder = _('Search...')


class ClearableFileInput(forms.ClearableFileInput):

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

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        output = ['<div class="drag-and-drop-wrapper">']
        output.append('<div class="drag-and-drop-placeholder"%s></div>' % (id and 'data-for="%s"' % id or ''))
        output.append('<div class="thumbnail-wrapper">')
        if value and isinstance(value, FieldFile):
            output.append(self._render_value(value))
        output.append('</div><div class=file-input-wrapper>')
        output.append(super(DragAndDropFileInput, self).render(name, value, attrs=attrs))
        output.append(2 * '</div>')
        return mark_safe('\n'.join(output))


class SmartWidgetMixin:

    def smart_render(self, request, name, value, initial_value, form, attrs=None, renderer=None):
        return self.render(name, value, attrs=attrs, renderer=renderer)


class ReadonlyWidget(SmartWidgetMixin, Widget):

    def __init__(self, widget=None, attrs=None):
        super().__init__(attrs)
        self.widget = widget

    def _get_widget(self):
        widget = self.widget
        while isinstance(widget, WrapperWidget):
            widget = widget.widget
        return widget

    def _get_value(self, value):
        widget = self._get_widget()
        if widget and hasattr(widget, 'choices'):
            choices_dict = dict(widget.choices)
            text_choices_dict = {str(k): v for k, v in widget.choices}
            return choices_dict.get(value, text_choices_dict.get(value, value))
        else:
            return value

    def _get_value_display(self, value, request=None):
        from is_core.utils import display_for_value

        value = self._get_value(value)

        if value in EMPTY_VALUES:
            value = EMPTY_VALUE

        return display_for_value(value, request=request)

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        return format_html('<p>{}</p>', self._get_value_display(value, request))

    def _render_readonly_value(self, readonly_value):
        return readonly_value.render()

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, ReadonlyValue):
            return self._render_readonly_value(value)
        else:
            return self._render_readonly(name, value, attrs, renderer)

    def smart_render(self, request, name, value, initial_value, form, attrs=None, renderer=None):
        return (
            self._render_readonly_value(value) if isinstance(value, ReadonlyValue)
            else self._render_readonly(name, value, attrs, renderer, request, form, initial_value)
        )

    def _has_changed(self, initial, data):
        return False


class JSONReadonlyWidget(ReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        return display_json(value)


class ModelObjectReadonlyWidget(ReadonlyWidget):

    def _render_object(self, request, obj, display_value=None):
        from is_core.utils import render_model_object_with_link

        return render_model_object_with_link(request, obj, display_value)

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if request and value and isinstance(value, Model):
            return format_html('<p>{}</p>', self._render_object(request, value))
        else:
            return super()._render_readonly(name, value, attrs, renderer, request, form, initial_value)


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

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if request and value and isinstance(value, (list, tuple)):
            return format_html_join(', ', '{}', ((self._render_object(request, obj),) for obj in value))
        else:
            return super()._render_readonly(name, value, attrs, renderer, request, form, initial_value)


class ModelChoiceReadonlyWidget(ModelObjectReadonlyWidget):

    def _choice(self, value):
        widget = self._get_widget()
        if hasattr(widget, 'choices'):
            return widget.choices.get_choice_from_value(value)

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if request and self._get_widget():
            choice = self._choice(value)
            if choice:
                rendered_value = self._render_object(request, choice.obj, force_text(choice[1]))
            elif value in EMPTY_VALUES:
                rendered_value = EMPTY_VALUE

            return format_html('<p>{}</p>', rendered_value)
        else:
            return super()._render_readonly(name, value, attrs, renderer, request, form, initial_value)


class ModelMultipleReadonlyWidget(ModelChoiceReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if request and isinstance(value, (list, tuple)) and self._get_widget():
            rendered_values = []
            for value_item in value:
                choice = self._choice(value_item)
                if choice:
                    value_item = force_text(choice[1])
                    if choice.obj:
                        rendered_values.append(self._render_object(request, choice.obj, value_item))
                    else:
                        rendered_values.append(value_item)
            return format_html(
                '<p>{}</p>',
                format_html_join(', ', '{}', ((v,) for v in rendered_values)) if rendered_values else EMPTY_VALUE
            )
        else:
            return super(ModelObjectReadonlyWidget, self)._render_readonly(
                name, value, attrs, renderer, request, form, initial_value
            )


class URLReadonlyWidget(ReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if value:
            return format_html('<a href="{}">{}</a>', value, value)
        else:
            return super()._render_readonly(name, value, attrs, renderer, request, form, initial_value)


class FileReadonlyWidget(ReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        if value and isinstance(value, FieldFile):
            return format_html('<a href="{}">{}</a>', value.url, os.path.basename(value.name))
        else:
            return super()._render_readonly(name, value, attrs, renderer, request, form, initial_value)


class EmptyWidget(ReadonlyWidget):

    def render(self, *args, **kwargs):
        return ''

    def smart_render(self, *args, **kwargs):
        return ''


class ButtonWidget(ReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        final_attrs = self.build_attrs(self.attrs, attrs, name=name)

        return format_html('<button %(attrs)s>%(value)s</button>' %
                           {'value': value, 'attrs': flatatt(final_attrs)})


class DivButtonWidget(ReadonlyWidget):

    def _render_readonly(self, name, value, attrs=None, renderer=None, request=None, form=None, initial_value=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        class_name = final_attrs.pop('class', '')
        return format_html('<div class="%(class_name)s btn btn-primary btn-small" '
                           '%(attrs)s>%(value)s</div>' %
                           {'class_name': class_name, 'value': value, 'attrs': flatatt(final_attrs)})


class MultipleTextInput(forms.TextInput):

    def __init__(self, attrs=None, separator=','):
        super().__init__(attrs)
        self.separator = separator

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, str):
            value = [value]
        return super().render(
            name, '{} '.format(self.separator).join(map(force_text, value)) if value else value, attrs, renderer
        )

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
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

    def render(self, name, value, attrs=None, renderer=None):
        if attrs and 'data-filter' in attrs:
            filter_term = attrs.pop('data-filter')
            for widget, operator in zip(self.widgets, ('gte', 'lt')):
                widget.attrs['data-filter'] = '{}__{}'.format(filter_term.rsplit('__', 1)[0], operator)
        return super().render(name, value, attrs, renderer)


class DateRangeFilterWidget(FilterDateRangeWidgetMixin, DateRangeWidget):
    pass


class DateTimeRangeFilterWidget(FilterDateRangeWidgetMixin, DateTimeRangeWidget):
    pass


class RestrictedSelectWidgetMixin:

    select_class_name = None
    select_placeholder = None
    input_placeholder = None

    @cached_property
    def is_restricted(self):
        """
        Returns True or False according to number of objects in queryset.
        If queryset contains too much objects the widget will be restricted and won't be used select box with choices.
        """
        return (
            not hasattr(self.choices, 'queryset') or
            settings.FOREIGN_KEY_MAX_SELECTBOX_ENTRIES == 0 or
            self.choices.queryset.values('pk')[:settings.FOREIGN_KEY_MAX_SELECTBOX_ENTRIES + 1].count()
            > settings.FOREIGN_KEY_MAX_SELECTBOX_ENTRIES
        )

    def render(self, name, value, attrs=None, renderer=None):
        if self.is_restricted:
            if value is None:
                value = ''
            final_attrs = self.build_attrs(self.attrs, attrs, type='text', name=name)
            if value != '':
                # Only add the 'value' attribute if a value is non-empty.
                final_attrs['value'] = self.format_resticted_value(value)
            final_attrs['placeholder'] = self.input_placeholder
            return format_html('<input{} />', flatatt(final_attrs))
        else:
            attrs = add_class_name(attrs, self.select_class_name)
            attrs['placeholder'] = self.select_placeholder
            return super().render(name, value, attrs, renderer)


class RestrictedSelectWidget(RestrictedSelectWidgetMixin, forms.Select):

    select_class_name = 'fulltext-search'
    select_placeholder = _('Search...')
    input_placeholder = _('Insert primary key')

    def format_resticted_value(self, value):
        return None if value is None else str(value)


class RestrictedSelectMultipleWidget(RestrictedSelectWidgetMixin, forms.SelectMultiple):

    select_class_name = 'fulltext-search-multiple'
    select_placeholder = _('Search...')
    input_placeholder = _('Insert primary keys separated by comma')

    def __init__(self, attrs=None, separator=','):
        super().__init__(attrs)
        self.separator = separator

    def value_from_datadict(self, data, files, name):
        if self.is_restricted:
            value = data.get(name)
            return [v.strip() for v in value.split(self.separator) if v.strip()] if isinstance(value, str) else value
        else:
            return super(RestrictedSelectMultipleWidget, self).value_from_datadict(data, files, name)

    def format_resticted_value(self, value):
        if value is None:
            value = []
        if not isinstance(value, (tuple, list)):
            value = [value]
        return self.separator.join([str(v) if v is not None else '' for v in value])
