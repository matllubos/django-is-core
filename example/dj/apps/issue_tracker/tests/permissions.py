from germanium.test_cases.default import GermaniumTestCase
from germanium.tools import assert_true, assert_false, assert_equal, assert_not_equal

from is_core.auth.permissions import BasePermission, PermissionsSet, SelfPermission


__all__ =(
    'PermissionsTestCase',
)


class ObjIsNonePermission(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return obj is None


class ObjIsNotNonePermission(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return obj is not None


class ObjIsStringPermission(BasePermission):

    def has_permission(self, name, request, view, obj=None):
        return isinstance(obj, str)


class PermissionsTestCase(GermaniumTestCase):

    def test_permissions_should_be_joined_with_operators(self):
        obj_is_none = ObjIsNonePermission()
        obj_is_not_none = ObjIsNotNonePermission()
        obj_is_string = ObjIsStringPermission()

        assert_true((obj_is_none | obj_is_not_none).has_permission('test', None, None, None))
        assert_true((obj_is_none | obj_is_not_none).has_permission('test', None, None, ''))
        assert_false((obj_is_none & obj_is_not_none).has_permission('test', None, None, None))
        assert_false((obj_is_none & obj_is_not_none).has_permission('test', None, None, ''))
        assert_true(((obj_is_none | obj_is_string) & obj_is_not_none).has_permission('test', None, None, ''))
        assert_true(((obj_is_none & obj_is_string) | obj_is_not_none).has_permission('test', None, None, ''))
        assert_false((obj_is_not_none | (obj_is_none & obj_is_string)).has_permission('test', None, None, None))
        assert_true((~obj_is_none).has_permission('test', None, None, ''))
        assert_false((~obj_is_not_none).has_permission('test', None, None, ''))
        assert_true((obj_is_none & ~obj_is_not_none).has_permission('test', None, None, None))

    def test_permissions_set_should_return_permissions_according_to_name(self):
        permission = PermissionsSet(
            none=ObjIsNonePermission(),
            not_none=ObjIsNotNonePermission(),
            string=ObjIsStringPermission(),
            self_note=SelfPermission('none'),
        )

        assert_true(permission.has_permission('none', None, None, None))
        assert_false(permission.has_permission('none', None, None, ''))
        assert_false(permission.has_permission('invalid', None, None, None))
        assert_false(permission.has_permission('not_none', None, None, None))
        assert_true(permission.has_permission('string', None, None, ''))
        assert_true(permission.has_permission('self_note', None, None, None))
        assert_false(permission.has_permission('self_note', None, None, ''))
