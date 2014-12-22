from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.query import ValuesListQuerySet
from django.db.models.base import Model
from django.forms.fields import FileField
from django.forms.forms import BoundField

from chamber.forms.widgets import ReadonlyWidget

from .fields import *
from .models import *


class ReadonlyBoundField(BoundField):

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        if not widget:
            widget = self.field.widget
        return super(ReadonlyBoundField, self).as_widget(self.form._get_readonly_widget(self.name, self.field,
                                                                                        widget), attrs, only_initial)


class SmartFormMixin(object):

    def __init__(self, *args, **kwargs):
        super(SmartFormMixin, self).__init__(*args, **kwargs)
        self._set_fields()

    def _set_fields(self):

        readonly_fields = getattr(self._meta, 'readonly_fields', ())
        exclude_fields = getattr(self._meta, 'exclude', ())

        for name, field in self.fields.items():
            if name in readonly_fields:
                field.is_readonly = True
            elif name in exclude_fields:
                del self.fields[name]

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)

        if field.is_readonly:
            return ReadonlyBoundField(self, field, name)
        else:
            return BoundField(self, field, name)

    def _get_readonly_widget(self, field_name, field, widget):
        return ReadonlyWidget(widget)

    def _clean_fields(self):
        for name, field in self.fields.items():
            if not field.is_readonly:
                # value_from_datadict() gets the data from the data dictionaries.
                # Each widget type knows how to retrieve its own data, because some
                # widgets split data over several HTML fields.
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                try:
                    if isinstance(field, FileField):
                        initial = self.initial.get(name, field.initial)
                        value = field.clean(value, initial)
                    else:
                        value = field.clean(value)
                    self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
                except ValidationError as e:
                    self._errors[name] = self.error_class(e.messages)
                    if name in self.cleaned_data:
                        del self.cleaned_data[name]
