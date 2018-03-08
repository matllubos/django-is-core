from django import forms
from django.utils.translation import ugettext_lazy as _

from is_core.forms import SmartForm

from class_based_auth_views.forms import AuthenticationMixin, AuthenticationCleanMixin


class TokenAuthenticationMixin(AuthenticationMixin):

    def __init__(self, *args, **kwargs):
        super(TokenAuthenticationMixin, self).__init__(*args, **kwargs)
        self.fields['permanent'] = forms.BooleanField(label=_('Remember user'), required=False)

    def is_permanent(self):
        return self.cleaned_data.get('permanent', False)


class TokenAuthenticationForm(TokenAuthenticationMixin, AuthenticationCleanMixin, SmartForm):
    pass