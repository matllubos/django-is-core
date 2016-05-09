from pyston.forms import RESTModelForm

from django import forms
from django.utils.translation import ugettext_lazy as _


class UserForm(RESTModelForm):
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)

    def __init__(self, instance=None, *args, **kwargs):
        super(UserForm, self).__init__(instance=instance, *args, **kwargs)
        if instance:
            self.fields['password'].required = False

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

    class Meta:
        exclude = ('last_login', 'password', 'is_staff', 'is_active', 'date_joined', 'groups', 'user_permissions')
