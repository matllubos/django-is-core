class BasePermission:
    """
    Base IS core permission object which has only one method has_permission which must be implemented in descendant.
    """

    def has_permission(self, name, request, view, obj=None):
        """
        Checks if request has permission to the given action.

        Args:
            name (str): name of the permission
            request (django.http.request.HttpRequest): Django request object
            view (object): Django view or REST view object
            obj (object): Object that is related with the given request

        Returns:
            True/False
        """
        raise NotImplementedError

    def __and__(self, other):
        assert isinstance(other, BasePermission), 'Only permission instances can be joined'

        return AndPermission(self, other)

    def __or__(self, other):
        assert isinstance(other, BasePermission), 'Only permission instances can be joined'

        return OrPermission(self, other)


class OperatorPermission(BasePermission):

    operator = None
    operator_function = None

    def __init__(self, *permissions):
        self._permissions = list(permissions)

    def has_permission(self, name, request, view, obj=None):
        return self.operator_function(
            permission.has_permission(name, request, view, obj=obj) for permission in self._permissions
        )

    def add(self, permission):
        assert isinstance(permission, BasePermission), 'Only permission instance can be added to the operator'

        self._permissions.append(permission)

    def __repr__(self):
        return '({})'.format(' {} '.format(self.operator).join(str(permission) for permission in self._permissions))

    def __iter__(self):
        for permission in self._permissions:
            yield permission


class AndPermission(OperatorPermission):
    """
    Helper for joining permissions with AND operator.
    """

    operator = '&'
    operator_function = all

    def __and__(self, other):
        assert isinstance(other, BasePermission), 'Only permission instances can be joined'

        self.add(other)
        return self


class OrPermission(OperatorPermission):
    """
    Helper for joining permissions with OR operator.
    """

    operator = '|'
    operator_function = any

    def __or__(self, other):
        assert isinstance(other, BasePermission), 'Only permission instances can be joined'

        self.add(other)
        return self


class PermissionsSet(BasePermission):
    """
    ``PermissionSet`` contains a set of permissions identified by name. Permission is granted if permission with the
    given name grants the access. Finally if no permission with the given name is found ``False`` is returned.
    """

    def __init__(self, **permissions_set):
        """
        Args:
            **permissions_set (BasePermission): permissions data
        """
        super().__init__()
        self._permissions = permissions_set

    def set(self, name, permission):
        """
        Adds permission with the given name to the set. Permission with the same name will be overridden.
        Args:
            name: name of the permission
            permission: permission instance
        """
        assert isinstance(permission, BasePermission), 'Only permission instances can be added to the set'

        self._permissions[name] = permission

    def has_permission(self, name, request, view, obj=None):
        permission = self._permissions.get(name, None)
        return permission is not None and permission.has_permission(name, request, view, obj=obj)

    def __iter__(self):
        for permission in self._permissions.values():
            yield permission


class IsAuthenticated(BasePermission):
    """
    Grant permission if user is authenticated and is active
    """

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_authenticated and request.user.is_active


class IsSuperuser(BasePermission):
    """
    Grant permission if user is superuser
    """

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_superuser


class IsAdminUser(BasePermission):
    """
    Grant permission if user is staff
    """

    def has_permission(self, name, request, view, obj=None):
        return request.user.is_staff


class AllowAny(BasePermission):
    """
    Grant permission every time
    """

    def has_permission(self, name, request, view, obj=None):
        return True


class CoreAllowed(BasePermission):
    """
    Grant permission if core permission with the name grants access
    """

    name = None

    def __init__(self, name=None):
        super().__init__()
        if name:
            self.name = name

    def has_permission(self, name, request, view, obj=None):
        return view.core.permission.has_permission(self.name or name, request, view, obj)


class CoreCreateAllowed(CoreAllowed):
    """
    Grant permission if core create permission grants access
    """

    name = 'create'


class CoreReadAllowed(CoreAllowed):
    """
    Grant permission if core read permission grants access
    """

    name = 'read'


class CoreUpdateAllowed(CoreAllowed):
    """
    Grant permission if core update permission grants access
    """

    name = 'update'


class CoreDeleteAllowed(CoreAllowed):
    """
    Grant permission if core delete permission grants access
    """

    name = 'delete'
