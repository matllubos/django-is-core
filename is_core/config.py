from django.conf import settings as django_settings


def _get_auth_login_view():
    if ('auth_token' in django_settings.INSTALLED_APPS
            and getattr(django_settings, 'AUTH_TOKEN_TWO_FACTOR_ENABLED', False)):
        return 'auth_token.contrib.is_core_auth.views.TwoFactorLoginView'
    elif 'auth_token' in django_settings.INSTALLED_APPS:
        return 'auth_token.contrib.is_core_auth.views.LoginView'
    else:
        return 'is_core.views.auth.LoginView'


DEFAULTS = {
    'AUTH_LOGIN_CODE_VERIFICATION_VIEW': (
        'auth_token.contrib.is_core_auth.views.LoginCodeVerificationView'
        if ('auth_token' in django_settings.INSTALLED_APPS
            and getattr(django_settings, 'AUTH_TOKEN_TWO_FACTOR_ENABLED', False))
        else None
    ),
    'AUTH_FORM_CLASS': (
        'auth_token.contrib.is_core_auth.forms.TokenAuthenticationSmartForm'
        if 'auth_token' in django_settings.INSTALLED_APPS
        else 'django.contrib.auth.forms.AuthenticationForm'
    ),
    'AUTH_RESOURCE_CLASS': None,
    'AUTH_LOGIN_VIEW': _get_auth_login_view(),
    'AUTH_LOGOUT_VIEW': (
        'auth_token.contrib.is_core_auth.views.LogoutView' if 'auth_token' in django_settings.INSTALLED_APPS
        else 'is_core.views.auth.LogoutView'
    ),
    'CODE_VERIFICATION_URL': '/login/login-code-verification/',
    'HOME_CORE': 'is_core.main.HomeUIISCore',
    'HOME_VIEW': 'is_core.generic_views.HomeView',
    'MENU_GENERATOR': 'is_core.menu.MenuGenerator',
    'USERNAME': 'username',
    'PASSWORD': 'password',
    'LOGIN_URL': '/login/',
    'LOGOUT_URL': '/logout/',
    'LOGIN_API_URL': lambda s: '/api{}'.format(s.LOGIN_URL),
    'EXPORT_TYPES': '',
    'FOREIGN_KEY_MAX_SELECTBOX_ENTRIES': 500,
    'LIST_PER_PAGE': 20,
    'REST_DEFAULT_FIELDS_EXTENSION': ('_rest_links',),
    'REST_PAGINATOR_MAX_TOTAL': 10000,
    'RESPONSE_EXCEPTION_FACTORY': 'is_core.exceptions.response.ui_rest_response_exception_factory',
    'DEFAULT_FIELDSET_TEMPLATE': 'is_core/forms/default_fieldset.html',
    'HEADER_IMAGE': None,
    'ENVIRONMENT': None,
    'BACKGROUND_EXPORT_TASK_TIME_LIMIT': 60*60,
    'BACKGROUND_EXPORT_TASK_SOFT_TIME_LIMIT': (60*60) - 5,
    'BACKGROUND_EXPORT_TASK_UPDATE_REQUEST_FUNCTION': None,
    'BACKGROUND_EXPORT_TASK_QUEUE': None,
    'BACKGROUND_EXPORT_SERIALIZATION_LIMIT': 2000,
    'BACKGROUND_EXPORT_STORAGE_CLASS': 'django.core.files.storage.DefaultStorage',
    'BACKGROUND_EXPORT_EXPIRATION_DAYS': 30,
}


class Settings:

    def __getattr__(self, attr):
        if attr not in DEFAULTS:
            raise AttributeError('Invalid IS_CORE setting: "{}"'.format(attr))

        default = DEFAULTS[attr]
        return getattr(django_settings, 'IS_CORE_{}'.format(attr), default(self) if callable(default) else default)


settings = Settings()
