
Permissions
===========

Main permissions goal is to often check if client has access to read/update/delete views. Implementation of `django-is-core` permissions system is very similar to DRF permissions. Base permission class is:

.. class:: is_core.auth.permissions.BasePermission

  Objects define structure of all permissions instances.

  .. method:: has_permission(name, request, view, obj=None)

    Method must be implemented for every permission object and should return True if all requirements was fulfilled to grant access to the client.
    First parameter name defines name of the wanted access, request is Django request object, view is Django view or REST resource and optional parameter obj is obj related with the given request.

Predefined permissions
----------------------

.. class:: is_core.auth.permissions.PermissionsSet

  ``PermissionSet`` contains a set of permissions identified by name. Permission is granted if permission with the given name grants the access. Finally if no permission with the given name is found ``False`` is returned.

.. class:: is_core.auth.permissions.IsAuthenticated

  Grants permission if user is authenticated and is active.

.. class:: is_core.auth.permissions.IsSuperuser

  Grants permission if user is authenticated, is active and is superuser.

.. class:: is_core.auth.permissions.IsAdminUser

  Grants permission if user is authenticated, is active and is staff.

.. class:: is_core.auth.permissions.AllowAny

  Grants permission every time.

.. class:: is_core.auth.permissions.CoreAllowed

  Grants permission if core (related with the view) permission selected according to the name grants the access.

.. class:: is_core.auth.permissions.CoreReadAllowed

  Grants permission if core read permission grant access.

.. class:: is_core.auth.permissions.CoreCreateAllowed

  Grants permission if core create permission grant access.

.. class:: is_core.auth.permissions.CoreUpdateAllowed

  Grants permission if core update permission grant access.

.. class:: is_core.auth.permissions.CoreDeleteAllowed

  Grants permission if core delete permission grant access.

.. class:: is_core.auth.permissions.AndPermission

  ``AndPermission`` is only helper for joining more permissions with ``AND`` operator. ``AndPermission`` init method accepts any number of permission instances and returns ``True`` if every inner permission returns ``True``::

    AndPermission(IsAdminUser(), IsSuperuser(), IsAuthenticated())

  Because this style of implementation is badly readable you can join permissions ``&``, the result will be the same::

    IsAdminUser() & IsSuperuser() & IsAuthenticated()

.. class:: is_core.auth.permissions.OrPermission

  ``OrPermission`` is same as ``AndPermission`` but permissions are joined with ``OR`` operator. ``OrPermission`` returns ``True`` if any inner permission returns ``True``. Again you can use joining with ``|`` operator::

    OrPermission(IsAdminUser(), IsSuperuser(), IsAuthenticated())
    IsAdminUser() | IsSuperuser() | IsAuthenticated()

.. class:: is_core.auth.permissions.NotPermission

  ``NotPermission`` can be used for permission negation. You can use operator ``~`` for the same purpose::

    NotPermission(IsAdminUser())
    ~IsAdminUser()


Custom permission
-----------------

If you want to implement custom permission, you only must create subclass of ``is_core.auth.permissions.BasePermission`` and implement ``has_permission`` method.

Core permissions
----------------

As an example of how to define core permissions we use model core of User object::

    from django.contrib.auth.models import User

    from is_core.auth.permissions import IsSuperuser
    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):

        model = User
        permission = IsSuperuser()


Now only a superuser has access to the User core. But this solution is a little bit dangerous, because there is no validated permission name and we only want create,read, update and delete permission names. Better solution is to use ``is_core.auth.permissions.PermissionsSet``::

    from django.contrib.auth.models import User

    from is_core.auth.permissions import PermissionsSet, IsSuperuser
    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):

        model = User
        permission = PermissionsSet(
            add=IsSuperuser(),
            read=IsSuperuser(),
            update=IsSuperuser(),
            delete=IsSuperuser(),
        )

Because writing too much code can lead to typos you can use ``default_permission`` attribute from which is automatically generated ``permission`` the result will be same as in previous example::

    from django.contrib.auth.models import User

    from is_core.auth.permissions import IsSuperuser
    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):

        model = User
        default_permission = IsSuperuser()

But if you want to disable for example deleting model instances the delete permission will not be added to the permission set::

    from django.contrib.auth.models import User

    from is_core.auth.permissions import IsSuperuser
    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):

        model = User
        default_permission = IsSuperuser()
        can_delete = False

the attribute permission will be now::

   permission = PermissionsSet(
       add=IsSuperuser(),
       read=IsSuperuser(),
       update=IsSuperuser(),
   )



You can use operator joining for using more permission types::

    from django.contrib.auth.models import User

    from is_core.auth.permissions import IsSuperuser, IsAdminUser
    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):

        model = User
        default_permission = IsSuperuser() & IsAdminUser()

For some cases is necessary update permissions in a class mixin for this purpose you can use method ``_init_permission(permission)`::

    from is_core.auth.permissions import IsSuperuser, IsAdminUser
    from is_core.main import UIRESTModelISCore


    class HistoryISCoreMixin:

        def _init_permission(self, permission):
            permission = super()._init_permission(permission)
            permission.set('history', IsSuperuser())
            return permission

    class UserISCore(UIRESTModelISCore):

        model = User
        permission = PermissionsSet(
            add=IsAdminUser(),
            read=IsAdminUser(),
            update=IsAdminUser(),
            delete=IsAdminUser(),
        )


View permissions
----------------

View permissions are used in the same way as core permissions::

    from is_core.auth.permissions import IsSuperuser
    from is_core.generic_views.form_views import ReadonlyDetailModelFormView

    class UserReadonlyDetailModelFormView(ReadonlyDetailModelFormView):

        permission = IsSuperuser()


Again you can set permissions according to names. For view permissions the names are HTTP method names::

    from is_core.auth.permissions import PermissionsSet, IsSuperuser
    from is_core.generic_views.form_views import DetailModelFormView

    class UserDetailModelFormView(DetailModelFormView):

        permission = PermissionsSet(
            post=IsSuperuser(),
            get=IsSuperuser()
        )

By default core views get access permissions from core. For example detail view permissions are set this way::

    from is_core.auth.permissions import PermissionsSet, CoreReadAllowed, CoreUpdateAllowed
    from is_core.generic_views.form_views import DetailModelFormView

    class UserDetailModelFormView(DetailModelFormView):

        permission = PermissionsSet(
            post=CoreUpdateAllowed(),
            get=CoreReadAllowed()
        )

If you want to have edit view accessible only if user is allowed to modify an object in core permissions. You can use very similar implementation::

    from is_core.auth.permissions import PermissionsSet, CoreUpdateAllowed
    from is_core.generic_views.form_views import DetailModelFormView

    class UserDetailModelFormView(DetailModelFormView):

        permission = PermissionsSet(
            post=CoreUpdateAllowed(),
            get=CoreUpdateAllowed()
        )


REST permissions
----------------

For the REST classes permissions you can use the same rules. The only difference is that there are more types of permissions because REST resource fulfills two functions - serializer and view (HTTP requests)::

    from is_core.rest.resource import RESTObjectPermissionsMixin

    class RESTModelCoreResourcePermissionsMixin(RESTObjectPermissionsMixin):

        permission = PermissionsSet(
            # HTTP permissions
            head=CoreReadAllowed(),
            options=CoreReadAllowed(),
            post=CoreCreateAllowed(),
            get=CoreReadAllowed(),
            put=CoreUpdateAllowed(),
            patch=CoreUpdateAllowed(),
            delete=CoreDeleteAllowed(),

            # Serializer permissions
            create_obj=CoreCreateAllowed(),
            read_obj=CoreReadAllowed(),
            update_obj=CoreUpdateAllowed(),
            delete_obj=CoreDeleteAllowed()
        )


Check permissions
-----------------

View/resource
^^^^^^^^^^^^^

If you want to check your custom permission in view or REST resource you can use method ``has_permission(name, obj=None)`` as an example we can use method ``is_readonly`` in th form view (form is readonly only if post permission returns ``False``)::


    def is_readonly(self):
        return not self.has_permission('post')


Because some permissions require obj parameter all views that inherit from ``is_core.generic_views.mixins.GetCoreObjViewMixin`` has automatically added objects to the permission check.


Core
^^^^

Sometimes you need to check permission in the core. But there is no view instance and you will have to create it. For better usability you can check permissions via view patterns, as an example we can use method ``get_list_actions`` which return edit action only if user has permission to update an object::

    def get_list_actions(self, request, obj):
        list_actions = super(UIRESTModelISCore, self).get_list_actions(request, obj)
        detail_pattern = self.ui_patterns.get('detail')
        if detail_pattern and detail_pattern.has_permission('get', request, obj=obj):
            return [
                WebAction(
                    'detail-{}'.format(self.get_menu_group_pattern_name()), _('Detail'),
                    'edit' if detail_pattern.has_permission('post', request, obj=obj) else 'detail'
                )
            ] + list(list_actions)
        else:
            return list_actions


Pattern method ``has_permission(name, request, obj=None, **view_kwargs)`` can be used with more ways. By default is ``view_kwargs`` get from request kwargs. If you can change it you can use method kwargs parameters. Parameter ``obj`` can be used for save system performance because object needn't be loaded from database again::

    detail_pattern = self.ui_patterns.get('detail')
    detail_pattern.has_permission('get', request)  # object id is get from request.kwargs
    detail_pattern.has_permission('get', request, id=obj.pk)  # request.kwargs "id" is overridden with obj.pk
    detail_pattern.has_permission('get', request, obj=obj)  # saves db queryes because object needn't be loaded from database

