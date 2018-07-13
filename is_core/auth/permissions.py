class BasePermission:

    def has_permission(self, name, request, view, obj=None):
        raise NotImplementedError


class PermissionsSet(BasePermission):

    def __init__(self, default_permission=None, **permissions_set):
        self._permissions = {}
        if default_permission:
            if not isinstance(default_permission, (list, tuple)):
                default_permission = [default_permission]
            self._permissions['__default__'] = default_permission
        for permission_name, permissions in permissions_set.items():
            if not isinstance(permissions, (list, tuple)):
                permissions = [permissions]
            self._permissions[permission_name] = list(permissions)

    def get_permissions(self):
        return self._permissions.values()

    def has_permission(self, name, request, view, obj=None):
        return any(
            permission.has_permission(name, request, view, obj=obj)
            for permission in self._permissions.get(name, self._permissions.get('__default__', ()))
        )


class IsAuthenticated(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_authenticated


class IsSuperuser(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_superuser


class IsAdminUser(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_staff


class AllowAny(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return True


class CoreAllowed:

    def __init__(self, name=None):
        self.name = name

    def has_permission(self, name, request, view, obj=None):
        return view.core.permissions.has_permission(self.name or name, request, view, obj)


class CoreReadAllowed:

    def has_permission(self, name, request, view, obj=None):
        return view.core.permissions.has_permission('read', request, view, obj)


class CoreCreateAllowed:

    def has_permission(self, name, request, view, obj=None):
        return view.core.permissions.has_permission('create', request, view, obj)


class CoreUpdateAllowed:

    def has_permission(self, name, request, view, obj=None):
        return view.core.permissions.has_permission('update', request, view, obj)


class CoreDeleteAllowed:

    def has_permission(self, name, request, view, obj=None):
        return view.core.permissions.has_permission('delete', request, view, obj)
