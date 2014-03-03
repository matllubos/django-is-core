from django.conf import settings

AUTH_FORM_CLASS = getattr(settings, 'AUTH_FORM_CLASS', 'django.contrib.auth.forms.AuthenticationForm')
AUTH_COOKIE_NAME = getattr(settings, 'AUTH_COOKIE_NAME', 'Authorization')
AUTH_HEADER_NAME = getattr(settings, 'AUTH_HEADER_NAME', 'HTTP_AUTHORIZATION')
AUTH_TOKEN_EXPIRATION = getattr(settings, 'AUTH_TOKEN_EXPIRATION', 60 * 60)
AUTH_USE_TOKENS = getattr(settings, 'AUTH_USE_TOKENS', False)
AUTH_LOGIN_VIEW = getattr(settings, 'AUTH_LOGIN_VIEW', AUTH_USE_TOKENS \
                                                        and 'is_core.auth_token.auth_views.TokenLoginView' \
                                                        or 'class_based_auth_views.views.LoginView')
AUTH_LOGOUT_VIEW = getattr(settings, 'AUTH_LOGOUT_VIEW', AUTH_USE_TOKENS \
                                                          and 'is_core.auth_token.auth_views.TokenLogoutView' \
                                                          or 'is_core.generic_views.auth_views.LoginView')

