from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from is_core.forms.widgets import ReadonlyWidget, EmptyWidget, DivButtonWidget


class ReadonlyField(forms.Field):
    widget = ReadonlyWidget
    readonly_widget = ReadonlyWidget

    is_readonly = True

    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=[], localize=False):
        super(ReadonlyField, self).__init__(required=False, widget=widget, label=label, initial=initial,
                                            help_text=help_text)

    def has_changed(self, initial, data):
        return False

    def validate(self, value):
        raise ValidationError(_('Readonly field can not be validated'))


class EmptyReadonlyField(ReadonlyField):
    widget = EmptyWidget
    readonly_widget = EmptyWidget

    def __init__(self):
        super(ReadonlyField, self).__init__()


class ButtonField(ReadonlyField):
    widget = DivButtonWidget
    readonly_widget = None

    def __init__(self, label, attrs=None, widget=None):
        attrs = attrs or {}
        widget = widget or self.widget
        super(ButtonField, self).__init__(required=False, label='', initial=label, widget=widget(attrs=attrs))


class SmartReadonlyField(ReadonlyField):

    def __init__(self, get_val_label_and_widget_fun, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=[], localize=False):
        self._get_val_label_and_widget_fun = get_val_label_and_widget_fun
        super(ReadonlyField, self).__init__(required=False, widget=widget, help_text=help_text)

    def _set_readonly_field(self, instance):
        self.initial, self.label, widget = self._get_val_label_and_widget_fun(instance)
        self.widget = widget()
        self.readonly_widget = widget()
