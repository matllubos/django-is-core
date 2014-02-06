from django.conf import settings

AUTH_FORM_CLASS = getattr(settings, 'AUTH_FORM_CLASS', 'django.contrib.auth.forms.AuthenticationForm')
