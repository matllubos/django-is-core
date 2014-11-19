from __future__ import unicode_literals

from django import forms


def formset_has_file_field(formset):
    for field in formset.base_fields.values():
        if isinstance(field, forms.FileField):
            return True
    return False
