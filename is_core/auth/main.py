from __future__ import unicode_literals


class PermissionsMixin(object):
    """
    Mixin that validate user permissions inside ISCore
    """

    def has_read_permission(self, request, obj=None):
        return True

    def has_create_permission(self, request, obj=None):
        return True

    def has_update_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class PermissionsUIMixin(PermissionsMixin):
    """
    Mixin that validate UI user permissions inside ISCore
    """

    def has_ui_read_permission(self, request, obj=None):
        return self.has_read_permission(request, obj)

    def has_ui_create_permission(self, request, obj=None):
        return self.has_create_permission(request, obj)

    def has_ui_update_permission(self, request, obj=None):
        return self.has_update_permission(request, obj)

    def has_ui_delete_permission(self, request, obj=None):
        return self.has_delete_permission(request, obj)


class PermissionsRESTMixin(PermissionsMixin):
    """
    Mixin that validate REST user permissions inside ISCore
    """

    def has_rest_read_permission(self, request, obj=None, via=None):
        return self.has_read_permission(request, obj)

    def has_rest_create_permission(self, request, obj=None, via=None):
        return self.has_create_permission(request, obj)

    def has_rest_update_permission(self, request, obj=None, via=None):
        return self.has_update_permission(request, obj)

    def has_rest_delete_permission(self, request, obj=None, via=None):
        return self.has_delete_permission(request, obj)