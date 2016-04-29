from __future__ import unicode_literals


class PermissionsMixin(object):
    """
    Mixin that validate user permissions inside ISCore
    """

    read_permission = True
    create_permission = True
    update_permission = True
    delete_permission = True

    def has_read_permission(self, request, obj=None):
        return self.read_permission

    def has_create_permission(self, request, obj=None):
        return self.create_permission

    def has_update_permission(self, request, obj=None):
        return self.update_permission

    def has_delete_permission(self, request, obj=None):
        return self.delete_permission


class PermissionsUIMixin(object):
    """
    Mixin that validate UI user permissions inside ISCore
    """

    ui_read_permission = None
    ui_create_permission = None
    ui_update_permission = None
    ui_delete_permission = None

    def has_ui_read_permission(self, request, obj=None):
        return (
            self.has_read_permission(request, obj) if self.ui_read_permission is None else self.ui_read_permission
        )

    def has_ui_create_permission(self, request, obj=None):
        return (
            self.has_create_permission(request, obj) if self.ui_create_permission is None else self.ui_create_permission
        )

    def has_ui_update_permission(self, request, obj=None):
        return (
            self.has_update_permission(request, obj) if self.ui_update_permission is None else self.ui_update_permission
        )

    def has_ui_delete_permission(self, request, obj=None):
        return (
            self.has_delete_permission(request, obj) if self.ui_delete_permission is None else self.ui_delete_permission
        )


class PermissionsRESTMixin(object):
    """
    Mixin that validate REST user permissions inside ISCore
    """

    rest_read_permission = None
    rest_create_permission = None
    rest_update_permission = None
    rest_delete_permission = None

    def has_rest_read_permission(self, request, obj=None, via=None):
        return (
            self.has_read_permission(request, obj)
            if self.rest_read_permission is None else self.rest_read_permission
        )

    def has_rest_create_permission(self, request, obj=None, via=None):
        return (
            self.has_create_permission(request, obj)
            if self.rest_create_permission is None else self.rest_create_permission
        )

    def has_rest_update_permission(self, request, obj=None, via=None):
        return (
            self.has_update_permission(request, obj)
            if self.rest_update_permission is None else self.rest_update_permission
        )

    def has_rest_delete_permission(self, request, obj=None, via=None):
        return (
            self.has_delete_permission(request, obj)
            if self.rest_delete_permission is None else self.rest_delete_permission
        )
