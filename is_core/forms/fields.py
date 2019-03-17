from django import forms
from django.core.exceptions import ValidationError
from django.db.models.base import Model
from django.utils.translation import ugettext

from is_core.forms.widgets import ReadonlyWidget, EmptyWidget, DivButtonWidget, ModelObjectReadonlyWidget

from .boundfield import ReadonlyBoundField


class ReadonlyField(forms.Field):

    widget = ReadonlyWidget
    readonly_widget = ReadonlyWidget

    is_readonly = True

    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=None, localize=False):
        super().__init__(required=False, widget=widget, label=label, initial=initial,
                                            help_text=help_text)

    def _has_changed(self, initial, data):
        return self.has_changed(initial, data)

    def has_changed(self, initial, data):
        return False

    def validate(self, value):
        raise ValidationError(ugettext('Readonly field can not be validated'))


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
        super().__init__(required=False, label='', initial=label, widget=widget(attrs=attrs))


class SmartReadonlyField(ReadonlyField):

    def __init__(self, get_val_label_and_widget_fun, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=None, localize=False):
        self._get_val_label_and_widget_fun = get_val_label_and_widget_fun
        super(ReadonlyField, self).__init__(required=False, widget=widget, help_text=help_text)

    def _set_readonly_field(self, name, form):
        self.initial, self.label, widget = self._get_val_label_and_widget_fun(form.instance)
        self.label = form._meta.labels.get(name, self.label) if form._meta.labels else self.label
        self.widget = widget()
        self.readonly_widget = ModelObjectReadonlyWidget() if isinstance(self.initial, Model) else widget()
