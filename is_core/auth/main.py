from is_core.auth import AuthWrapper

class PermissionsMiddleware(object):
    pass


class UIMiddleware(PermissionsMiddleware):

    def get_auth_wrapper(self, permissions_validators):
        return AuthWrapper(permissions_validators).wrap

    def has_read_permission(self, request):
        return True

    def has_create_permission(self, request):
        return True

    def has_update_permission(self, request):
        return True

    def has_delete_permission(self, request):
        return True
