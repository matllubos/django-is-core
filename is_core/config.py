from django.conf import settings as django_settings


DEFAULTS = {
    'AUTH_FORM_CLASS': (
        'auth_token.contrib.is_core_auth.forms.TokenAuthenticationSmartForm'
        if 'auth_token' in django_settings.INSTALLED_APPS
        else 'django.contrib.auth.forms.AuthenticationForm'
    ),
    'AUTH_RESOURCE_CLASS': (
        'auth_token.contrib.is_core_auth.resource.AuthResource' if 'auth_token' in django_settings.INSTALLED_APPS
        else None
    ),
    'AUTH_LOGIN_VIEW': (
        'auth_token.contrib.is_core_auth.views.LoginView' if 'auth_token' in django_settings.INSTALLED_APPS
        else 'is_core.views.auth.LoginView'
    ),
    'AUTH_LOGOUT_VIEW': (
        'auth_token.contrib.is_core_auth.views.LogoutView' if 'auth_token' in django_settings.INSTALLED_APPS
        else 'is_core.views.auth.LogoutView'
    ),
    'HOME_CORE': 'is_core.main.HomeUIISCore',
    'HOME_VIEW': 'is_core.generic_views.HomeView',
    'MENU_GENERATOR': 'is_core.menu.MenuGenerator',
    'USERNAME': 'username',
    'PASSWORD': 'password',
    'LOGIN_URL': '/login/',
    'LOGOUT_URL': '/logout/',
    'LOGIN_API_URL': lambda s: '/api{}'.format(s.LOGIN_URL),
    'EXPORT_TYPES': '',
    'FOREIGN_KEY_MAX_SELECBOX_ENTRIES': 500,
    'LIST_PER_PAGE': 20,
    'REST_DEFAULT_FIELDS_EXTENSION': ('_rest_links',),
    'RESPONSE_EXCEPTION_FACTORY': 'is_core.exceptions.response.ui_rest_response_exception_factory',
}


class Settings:

    def __getattr__(self, attr):
        if attr not in DEFAULTS:
            raise AttributeError('Invalid IS_CORE setting: "{}"'.format(attr))

        default = DEFAULTS[attr]
        return getattr(django_settings, 'IS_CORE_{}'.format(attr), default(self) if callable(default) else default)


settings = Settings()
