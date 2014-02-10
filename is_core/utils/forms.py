from django import forms


def formset_has_file_field(fromset):
    for field in fromset.base_fields.values():
        if isinstance(field, forms.FileField):
            return True
    return False
