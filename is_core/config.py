from django.conf import settings

AUTH_COOKIE_NAME = getattr(settings, 'AUTH_COOKIE_NAME', 'Authorization')
# Age of cookie, in seconds (default: 2 weeks).
AUTH_COOKIE_AGE = getattr(settings, 'AUTH_COOKIE_AGE', 60 * 60 * 24 * 7 * 2)
AUTH_COOKIE_HTTPONLY = getattr(settings, 'AUTH_COOKIE_HTTPONLY', False)
AUTH_COOKIE_SECURE = getattr(settings, 'AUTH_COOKIE_SECURE', False)
AUTH_HEADER_NAME = getattr(settings, 'AUTH_HEADER_NAME', 'HTTP_AUTHORIZATION')
# Default token expiration time (default: 1 hour)
AUTH_DEFAULT_TOKEN_AGE = getattr(settings, 'AUTH_DEFAULT_TOKEN_AGE', 60 * 60)
# Max token expiration time (default: 2 weeks)
AUTH_MAX_TOKEN_AGE = getattr(settings, 'AUTH_MAX_TOKEN_AGE', 60 * 60 * 24 * 7 * 2)
AUTH_COUNT_USER_PRESERVED_TOKENS = getattr(settings, 'AUTH_COUNT_USER_PRESERVED_TOKENS', 20)
AUTH_USE_TOKENS = getattr(settings, 'AUTH_USE_TOKENS', False)
AUTH_FORM_CLASS = getattr(settings, 'AUTH_FORM_CLASS', AUTH_USE_TOKENS and
                          'is_core.auth_token.forms.TokenAuthenticationForm' or
                          'django.contrib.auth.forms.AuthenticationForm')
AUTH_LOGIN_VIEW = getattr(settings, 'AUTH_LOGIN_VIEW', AUTH_USE_TOKENS \
                                                        and 'is_core.auth_token.auth_views.TokenLoginView' \
                                                        or 'class_based_auth_views.views.LoginView')
AUTH_LOGOUT_VIEW = getattr(settings, 'AUTH_LOGOUT_VIEW', AUTH_USE_TOKENS \
                                                          and 'is_core.auth_token.auth_views.TokenLogoutView' \
                                                          or 'is_core.generic_views.auth_views.LoginView')
HOME_IS_CORE = getattr(settings, 'HOME_IS_CORE', 'is_core.main.HomeUIISCore')
HOME_VIEW = getattr(settings, 'HOME_VIEW', 'is_core.generic_views.HomeView')
MENU_GENERATOR = getattr(settings, 'MENU_GENERATOR', 'is_core.menu.MenuGenerator')

USERNAME = getattr(settings, 'USERNAME', 'username')
PASSWORD = getattr(settings, 'PASSWORD', 'password')

LOGOUT_URL = getattr(settings, 'LOGOUT_URL', '/logout')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/login')
LOGIN_API_URL = getattr(settings, 'LOGIN_API_URL', '/api/%s' % LOGIN_URL[1:])

GRID_EXPORT = getattr(settings, 'GRID_EXPORT', '')

CORE_LOGIN_THROTTLING_VALIDATORS = getattr(settings, 'CORE_LOGIN_THROTTLING_VALIDATORS',
                                           'is_core.auth_token.auth_security.default_login_validators.validators')

AUTH_RESOURCE_CLASS = getattr(settings, 'AUTH_RESOURCE_CLASS', 'is_core.auth_token.auth_resource.AuthResource')
