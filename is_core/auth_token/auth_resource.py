try:
    import security
    from .auth_security.resource import AuthResource
except ImportError:
    from .default.resource import AuthResource