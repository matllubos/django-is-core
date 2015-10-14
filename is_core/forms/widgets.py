from __future__ import unicode_literals

import os

from itertools import chain

from django import forms
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join, conditional_escape
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.files import FieldFile
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Widget
from django.forms.utils import flatatt
from django.core.validators import EMPTY_VALUES
from django.db.models.base import Model


try:
    from sorl.thumbnail import default
except ImportError:
    default = None


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

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(extra_attrs=None, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)

    def render(self, name, value, attrs=None):
        return self.widget.render(name, value, attrs)


class SelectMixin(object):

    def render_option(self, selected_choices, option_value, option_label, option_attrs):
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html('<option value="{0}"{1}{2}>{3}</option>',
                           option_value,
                           selected_html,
                           flat_data_attrs(option_attrs) or '',
                           force_text(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for choice in chain(self.choices, choices):
            option_value, option_label = choice
            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{0}">', force_text(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_value, option_label, choice.attrs))
        return '\n'.join(output)


class Select(SelectMixin, forms.Select):

    class_name = 'fulltext-search'
    placeholder = _('Search...')


class MultipleSelect(SelectMixin, forms.SelectMultiple):

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


class SmartWidgetMixin(object):

    def smart_render(self, request, name, value, initial_value, *args, **kwargs):
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
        from is_core.utils import display_for_value

        widget = self._get_widget()
        if widget and hasattr(widget, 'choices'):
            result = dict(self.widget.choices).get(value)
        else:
            result = value

        if result in EMPTY_VALUES:
            result = EMPTY_VALUE

        return display_for_value(result)

    def _render(self, name, value, attrs=None, choices=()):
        if isinstance(value, (list, tuple)):
            out = ', '.join([self._get_value(val) for val in value])
        else:
            out = self._get_value(value)
        return mark_safe('<p>%s</p>' % conditional_escape(out))

    def _smart_render(self, request, name, value, initial_value, attrs=None, choices=()):
        return self._render(name, value, attrs, choices)

    def _render_readonly_value(self, readonly_value):
        return mark_safe('<p><span title="%s">%s</span></p>' % (conditional_escape(force_text(readonly_value.value)),
                                                                conditional_escape(readonly_value.humanized_value)))

    def render(self, name, value, attrs=None, choices=()):
        from is_core.forms.forms import ReadonlyValue

        if isinstance(value, ReadonlyValue):
            return self._render_readonly_value(value)
        else:
            return self._render(name, value, attrs, choices)

    def smart_render(self, request, name, value, initial_value, attrs=None, choices=()):
        from is_core.forms.forms import ReadonlyValue

        if isinstance(value, ReadonlyValue):
            return self._render_readonly_value(value)
        else:
            return self._smart_render(request, name, value, initial_value, attrs, choices)

    def _has_changed(self, initial, data):
        return False


class ModelObjectReadonlyWidget(ReadonlyWidget):

    def _get_obj_url(self, request, obj):
        from is_core.utils import get_obj_url

        return get_obj_url(request, obj)

    def _render_object(self, request, obj, display_value=None):
        from is_core.utils import render_model_object_with_link

        return render_model_object_with_link(request, obj, display_value)

    def _smart_render(self, request, name, value, initial_value, *args, **kwargs):
        if value and isinstance(value, Model):
            return mark_safe('<p>%s</p>' % self._render_object(request, value))
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(self, request, name, value, initial_value,
                                                                        *args, **kwargs)


class ManyToManyReadonlyWidget(ModelObjectReadonlyWidget):

    def _smart_render(self, request, name, value, initial_value, *args, **kwargs):
        if value and isinstance(value, (list, tuple)):
            return mark_safe(', '.join((self._render_object(request, obj) for obj in value)))
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(self, request, name, value, initial_value,
                                                                        *args, **kwargs)


class ModelChoiceReadonlyWidget(ModelObjectReadonlyWidget):

    def _get_choice(self, value):
        widget = self._get_widget()
        if hasattr(widget, 'choices'):
            for choice in widget.choices:
                if choice[0] == value:
                    return choice

    def _smart_render(self, request, name, value, initial_value, attrs=None, choices=()):
        choice = self._get_choice(value)

        out = []
        if choice:
            value = force_text(choice[1])
            if choice.obj:
                value = self._render_object(request, choice.obj, value) or value

        else:
            if value in EMPTY_VALUES:
                value = EMPTY_VALUE

        out.append(value)
        return mark_safe('<p>%s</p>' % '\n'.join(out))


class ModelMultipleReadonlyWidget(ModelChoiceReadonlyWidget):

    def _smart_render(self, request, name, values, initial_values, *args, **kwargs):
        if values and isinstance(values, (list, tuple)):
            rendered_values = []
            for value in values:
                choice = self._get_choice(value)
                if choice:
                    value = force_text(choice[1])
                    if choice.obj:
                        rendered_values.append(self._render_object(request, choice.obj, value))
                    else:
                        rendered_values.append(value)
            return mark_safe('<p>%s</p>' % rendered_values and ', '.join(rendered_values) or EMPTY_VALUE)
        else:
            return super(ModelObjectReadonlyWidget, self)._smart_render(request, name, values, initial_values,
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


class ButtonWidget(ReadonlyWidget):

    def _render(self, name, value, attrs=None, *args, **kwargs):
        final_attrs = self.build_attrs(attrs, name=name)

        return format_html('<button %(attrs)s>%(value)s</button>' %
                           {'value': value, 'attrs': flatatt(final_attrs)})


class DivButtonWidget(ReadonlyWidget):

    def _render(self, name, value, attrs=None, *args, **kwargs):
        final_attrs = self.build_attrs(attrs)
        class_name = final_attrs.pop('class', '')
        return format_html('<div class="%(class_name)s btn btn-primary btn-small" '
                           '%(attrs)s>%(value)s</div>' %
                           {'class_name': class_name, 'value': value, 'attrs': flatatt(final_attrs)})
