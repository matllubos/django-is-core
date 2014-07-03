from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.query import ValuesListQuerySet
from django.db.models.base import Model

from .fields import *
from .models import *


class RestFormMixin(object):

    def is_invalid(self):
        '''
        Validate input data. It uses django forms
        '''
        errors = {}
        if not self.is_valid():
            errors = dict([(k, v[0]) for k, v in self.errors.items()])

        if '__all__' in errors:
            del errors['__all__']

        non_field_errors = self.non_field_errors()
        if non_field_errors:
            errors['non-field-errors'] = non_field_errors

        if errors:
            return errors

        return False

    def is_valid(self):
        self._merge_from_initial()
        return super(RestFormMixin, self).is_valid()

    """
    Subclass of `forms.ModelForm` which makes sure
    that the initial values are present in the form
    data, so you don't have to send all old values
    for the form to actually validate. Django does not
    do this on its own, which is really annoying.
    """
    def _merge_from_initial(self):
        filt = lambda v: v not in self.data.keys()
        for field_name in filter(filt, self.fields.keys()):
            field = self.fields[field_name]

            self.data[field_name] = field.prepare_value(self.initial.get(field, field.initial))


class AllFieldsUniqueValidationModelForm(forms.ModelForm):

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)


class RestModelForm(RestFormMixin, AllFieldsUniqueValidationModelForm):
    pass
