from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError

from .fields import *
from .models import *


class AllFieldsUniqueValidationModelForm(forms.ModelForm):

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)


class RestFormMixin(object):

    def is_invalid(self):
        '''
        Validate input data. It uses django forms
        '''
        errors = {}
        if not self.is_valid():
            errors = dict([(k, v[0]) for k, v in self.errors.items()])

        non_field_errors = self.non_field_errors()
        if non_field_errors:
            errors = errors['non-field-errors'] = non_field_errors

        if errors:
            return errors

        return False


class RestModelForm(RestFormMixin, AllFieldsUniqueValidationModelForm):
    pass
