from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from is_core.forms.widgets import ReadonlyWidget, EmptyWidget, ButtonWidget


class ReadonlyField(forms.Field):
    widget = ReadonlyWidget
    readonly_widget = ReadonlyWidget

    is_readonly = True

    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=[], localize=False):
        super(ReadonlyField, self).__init__(required=False, widget=widget, label=label, initial=initial,
                                            help_text=help_text)

    def _has_changed(self, initial, data):
        return False

    def validate(self, value):
        raise ValidationError(_('Readonly field can not be validated'))


class EmptyReadonlyField(ReadonlyField):
    widget = EmptyWidget
    readonly_widget = EmptyWidget

    def __init__(self):
        super(ReadonlyField, self).__init__()


class ButtonField(ReadonlyField):
    widget = ButtonWidget
    readonly_widget = None

    def __init__(self, label, attrs):
        super(ButtonField, self).__init__(required=False, label='', initial=label, widget=ButtonWidget(attrs=attrs))


class SmartReadonlyField(ReadonlyField):

    def __init__(self, get_val_and_label_fun, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=[], localize=False):
        self._get_val_and_label_fun = get_val_and_label_fun
        super(ReadonlyField, self).__init__(required=False, widget=widget, help_text=help_text)

    def _set_val_and_label(self, instance):
        self.initial, self.label = self._get_val_and_label_fun(instance)

