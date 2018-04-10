from django.conf import settings as django_settings


DEFAULTS = {
    'AUTH_COOKIE_NAME': 'Authorization',
    'AUTH_COOKIE_AGE': 60 * 60 * 24 * 7 * 2,  # Age of cookie, in seconds (default: 2 weeks)
    'AUTH_COOKIE_HTTPONLY': False,
    'AUTH_COOKIE_SECURE': False,
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_HEADER_NAME': 'Authorization',
    'AUTH_HEADER_TOKEN_TYPE': 'Bearer',
    'AUTH_DEFAULT_TOKEN_AGE': 60 * 60,  # Default token expiration time (default: 1 hour)
    'AUTH_MAX_TOKEN_AGE': 60 * 60 * 24 * 7 * 2,  # Max token expiration time (default: 2 weeks)
    'AUTH_COUNT_USER_PRESERVED_TOKENS': 20,
    'AUTH_USE_TOKENS': False,
    'AUTH_FORM_CLASS': lambda s: ('is_core.auth_token.forms.TokenAuthenticationForm' if s.AUTH_USE_TOKENS
                                  else 'django.contrib.auth.forms.AuthenticationForm'),
    'AUTH_RESOURCE_CLASS': 'is_core.auth_token.auth_resource.AuthResource',
    'AUTH_LOGIN_VIEW': lambda s: ('is_core.auth_token.auth_views.TokenLoginView' if s.AUTH_USE_TOKENS
                                  else 'class_based_auth_views.views.LoginView'),
    'AUTH_LOGOUT_VIEW': lambda s: ('is_core.auth_token.auth_views.TokenLogoutView' if s.AUTH_USE_TOKENS
                                   else 'is_core.generic_views.auth_views.LogoutView'),
    'AUTH_TAKEOVER_REDIRECT_URL': '/',
    'HOME_CORE': 'is_core.main.HomeUIISCore',
    'HOME_VIEW': 'is_core.generic_views.HomeView',
    'MENU_GENERATOR': 'is_core.menu.MenuGenerator',
    'USERNAME': 'username',
    'PASSWORD': 'password',
    'LOGIN_URL': django_settings.LOGIN_URL,
    'LOGOUT_URL': '/logout/',
    'LOGIN_API_URL': lambda s: '/api{}'.format(s.LOGIN_URL),
    'EXPORT_TYPES': '',
    'FOREIGN_KEY_MAX_SELECBOX_ENTRIES': 500,
    'LIST_PER_PAGE': 20,
    'AUTH_TOKEN_RENEWAL_EXEMPT_HEADER': 'X-Authorization-Renewal-Exempt',
    'AUTH_TOKEN_EXPIRATION_HEADER': 'X-Authorization-Expiration',
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
