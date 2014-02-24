from django.conf import settings

AUTH_FORM_CLASS = getattr(settings, 'AUTH_FORM_CLASS', 'django.contrib.auth.forms.AuthenticationForm')
AUTH_COOKIE_NAME = getattr(settings, 'AUTH_COOKIE_NAME', 'Authorization')
AUTH_HEADER_NAME = getattr(settings, 'AUTH_HEADER_NAME', 'HTTP_AUTHORIZATION')
AUTH_TOKEN_EXPIRATION = getattr(settings, 'AUTH_TOKEN_EXPIRATION', 60 * 60)
AUTH_USE_TOKENS = getattr(settings, 'AUTH_USE_TOKENS', False)
