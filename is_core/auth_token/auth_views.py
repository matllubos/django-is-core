from .default.views import TokenLogoutView

try:
    import security
    from .auth_security.views import TokenLoginView
except ImportError as er:
    from .default.views import TokenLoginView
