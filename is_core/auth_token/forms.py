from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm


class RESTAuthenticationForm(AuthenticationForm):

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


class TokenAuthenticationForm(RESTAuthenticationForm):
    permanent = forms.BooleanField(label=_('Remember user'), required=False)

    def is_permanent(self):
        return self.cleaned_data.get('permanent', False)
