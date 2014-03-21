from __future__ import unicode_literals

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _


class TokenAuthenticationForm(AuthenticationForm):
    permanent = forms.BooleanField(label=_('Remember user'), required=False)

    def is_permanent(self):
        return self.cleaned_data.get('permanent', False)
