from germanium.test_cases.default import GermaniumTestCase
from germanium.tools import assert_true, assert_false, assert_equal, assert_not_equal

from is_core.auth.permissions import FieldsListPermission, FieldsSetPermission, PermissionsSet, AllowAny

from .permissions import ObjIsNotNonePermission


__all__ =(
    'FieldPermissionsTestCase',
)


class FieldPermissionsTestCase(GermaniumTestCase):

    def test_fields_list_permission_sould_return_right_disallowed_fields(self):
        field_list_permission = FieldsListPermission(
            permission=PermissionsSet(
                read=ObjIsNotNonePermission()
            ),
            fields=('a', 'b', 'c')
        )
        assert_equal(
            field_list_permission.get_disallowed_fields(None, None, None),
            {'a', 'b', 'c'}
        )
        assert_equal(
            field_list_permission.get_disallowed_fields(None, None, ''),
            set()
        )

    def test_fields_list_permission_sould_return_right_readonly_fields(self):
        field_list_permission = FieldsListPermission(
            permission=PermissionsSet(
                read=AllowAny(),
                edit=ObjIsNotNonePermission()
            ),
            fields=('a', 'b', 'c')
        )
        assert_equal(
            field_list_permission.get_readonly_fields(None, None, None),
            {'a', 'b', 'c'}
        )
        assert_equal(
            field_list_permission.get_readonly_fields(None, None, ''),
            set()
        )

    def test_fields_set_permission_sould_return_right_disallowed_fields(self):
        field_set_permission = FieldsSetPermission(
            FieldsListPermission(
                permission=PermissionsSet(
                    read=ObjIsNotNonePermission()
                ),
                fields=('a', 'b', 'c')
            ),
            FieldsListPermission(
                permission=PermissionsSet(
                    read=AllowAny(),
                    edit=ObjIsNotNonePermission()
                ),
                fields=('a', 'b', 'd')
            ),
            FieldsListPermission(
                permission=PermissionsSet(
                    read=ObjIsNotNonePermission()
                ),
                fields=('e',)
            ),
        )
        assert_equal(
            field_set_permission.get_disallowed_fields(None, None, None),
            {'a', 'b', 'c', 'e'}
        )
        assert_equal(
            field_set_permission.get_disallowed_fields(None, None, ''),
            set()
        )

    def test_fields_set_permission_sould_return_right_readonly_fields(self):
        field_set_permission = FieldsSetPermission(
            FieldsListPermission(
                permission=PermissionsSet(
                    read=ObjIsNotNonePermission()
                ),
                fields=('a', 'b', 'c')
            ),
            FieldsListPermission(
                permission=PermissionsSet(
                    read=AllowAny(),
                    edit=ObjIsNotNonePermission()
                ),
                fields=('a', 'b', 'd')
            ),
            FieldsListPermission(
                permission=PermissionsSet(
                    read=ObjIsNotNonePermission()
                ),
                fields=('e',)
            ),
        )
        assert_equal(
            field_set_permission.get_readonly_fields(None, None, None),
            {'a', 'b', 'c', 'd', 'e'}
        )
        assert_equal(
            field_set_permission.get_readonly_fields(None, None, ''),
            {'a', 'b', 'c', 'e'}
        )
