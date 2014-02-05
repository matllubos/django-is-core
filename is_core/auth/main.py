from is_core.auth import AuthWrapper

class PermissionsMiddleware(object):
    pass


class UIMiddleware(PermissionsMiddleware):

    def get_auth_wrapper(self, permissions_validators):
        return AuthWrapper(permissions_validators).wrap
