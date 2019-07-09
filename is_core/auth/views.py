class FieldPermissionViewMixin:

    field_permissions = None

    def _get_field_permissions(self):
        return self.field_permissions if self.field_permissions is not None else self.core.field_permissions

    def _get_disallowed_fields_from_permissions(self, obj=None):
        return self._get_field_permissions().get_disallowed_fields(self.request, self, obj=obj)

    def _get_readonly_fields_from_permissions(self, obj=None):
        return self._get_field_permissions().get_readonly_fields(self.request, self, obj=obj)
