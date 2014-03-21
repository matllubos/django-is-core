from __future__ import unicode_literals

from is_core.auth import AuthWrapper


class PermissionsMixin(object):
    """
    Mixin that validate user permissions inside ISCore
    """

    def has_read_permission(self, request, pk=None):
        return True

    def has_create_permission(self, request, pk=None):
        return True

    def has_update_permission(self, request, pk=None):
        return True

    def has_delete_permission(self, request, pk=None):
        return True


class PermissionsUIMixin(PermissionsMixin):
    """
    Mixin that validate UI user permissions inside ISCore
    """

    def get_auth_wrapper(self, permissions_validators):
        return AuthWrapper(permissions_validators).wrap

    def has_ui_read_permission(self, request, pk=None):
        return self.has_read_permission(request, pk)

    def has_ui_create_permission(self, request, pk=None):
        return self.has_create_permission(request, pk)

    def has_ui_update_permission(self, request, pk=None):
        return self.has_update_permission(request, pk)

    def has_ui_delete_permission(self, request, pk=None):
        return self.has_delete_permission(request, pk)


class PermissionsRestMixin(PermissionsMixin):
    """
    Mixin that validate REST user permissions inside ISCore
    """

    def has_rest_read_permission(self, request, pk=None):
        return self.has_read_permission(request, pk)

    def has_rest_create_permission(self, request, pk=None):
        return self.has_create_permission(request, pk)

    def has_rest_update_permission(self, request, pk=None):
        return self.has_update_permission(request, pk)

    def has_rest_delete_permission(self, request, pk=None):
        return self.has_delete_permission(request, pk)
