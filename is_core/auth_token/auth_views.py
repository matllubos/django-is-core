from .default.views import TokenLogoutView

try:
    import security
    from .auth_security.views import TokenLoginView
except ImportError as er:
    print er
    from .default.views import TokenLoginView
