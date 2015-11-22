from django.conf import settings

IS_CORE_AUTH_COOKIE_NAME = getattr(settings, 'IS_CORE_AUTH_COOKIE_NAME', 'Authorization')
# Age of cookie, in seconds (default: 2 weeks).
IS_CORE_AUTH_COOKIE_AGE = getattr(settings, 'IS_CORE_AUTH_COOKIE_AGE', 60 * 60 * 24 * 7 * 2)
IS_CORE_AUTH_COOKIE_HTTPONLY = getattr(settings, 'IS_CORE_AUTH_COOKIE_HTTPONLY', False)
IS_CORE_AUTH_COOKIE_SECURE = getattr(settings, 'IS_CORE_AUTH_COOKIE_SECURE', False)
IS_CORE_AUTH_HEADER_NAME = getattr(settings, 'IS_CORE_AUTH_HEADER_NAME', 'Authorization')
# Default token expiration time (default: 1 hour)
IS_CORE_AUTH_DEFAULT_TOKEN_AGE = getattr(settings, 'IS_CORE_AUTH_DEFAULT_TOKEN_AGE', 60 * 60)
# Max token expiration time (default: 2 weeks)
IS_CORE_AUTH_MAX_TOKEN_AGE = getattr(settings, 'IS_CORE_AUTH_MAX_TOKEN_AGE', 60 * 60 * 24 * 7 * 2)
IS_CORE_AUTH_USE_TOKENS = 'is_core.auth_token' in settings.INSTALLED_APPS
IS_CORE_AUTH_FORM_CLASS = getattr(settings, 'IS_CORE_AUTH_FORM_CLASS', IS_CORE_AUTH_USE_TOKENS and
                                  'is_core.auth_token.forms.TokenAuthenticationForm' or
                                  'django.contrib.auth.forms.AuthenticationForm')
IS_CORE_AUTH_LOGIN_VIEW = getattr(settings, 'IS_CORE_AUTH_LOGIN_VIEW', IS_CORE_AUTH_USE_TOKENS and
                                  'is_core.auth_token.auth_views.TokenLoginView' or
                                  'class_based_auth_views.views.LoginView')
IS_CORE_AUTH_LOGOUT_VIEW = getattr(settings, 'IS_CORE_AUTH_LOGOUT_VIEW',
                                   IS_CORE_AUTH_USE_TOKENS and 'is_core.auth_token.auth_views.TokenLogoutView' or
                                   'is_core.generic_views.auth_views.LoginView')
IS_CORE_HOME_CORE = getattr(settings, 'IS_CORE_HOME_CORE', 'is_core.main.HomeUIISCore')
IS_CORE_HOME_VIEW = getattr(settings, 'IS_CORE_HOME_VIEW', 'is_core.generic_views.HomeView')
IS_CORE_MENU_GENERATOR = getattr(settings, 'IS_CORE_MENU_GENERATOR', 'is_core.menu.MenuGenerator')

IS_CORE_USERNAME = getattr(settings, 'IS_CORE_USERNAME', 'username')
IS_CORE_PASSWORD = getattr(settings, 'IS_CORE_PASSWORD', 'password')

IS_CORE_LOGOUT_URL = getattr(settings, 'IS_CORE_LOGOUT_URL', settings.LOGOUT_URL)
IS_CORE_LOGIN_URL = getattr(settings, 'IS_CORE_LOGIN_URL', settings.LOGIN_URL)
IS_CORE_LOGIN_API_URL = getattr(settings, 'IS_CORE_LOGIN_API_URL', '/api/%s' % IS_CORE_LOGIN_URL[1:])

IS_CORE_EXPORT_TYPES = getattr(settings, 'IS_CORE_EXPORT_TYPES', '')


IS_CORE_LOGIN_THROTTLING_VALIDATORS = getattr(settings, 'IS_CORE_LOGIN_THROTTLING_VALIDATORS',
                                              'is_core.auth_token.auth_security.default_login_validators.validators')
