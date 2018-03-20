from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelForm
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet as OriginBaseGenericInlineFormSet

from is_core.forms.models import smartmodelformset_factory
from is_core.forms.formsets import BaseFormSetMixin


class BaseGenericInlineFormSet(BaseFormSetMixin, OriginBaseGenericInlineFormSet):
    pass


def smartgeneric_inlineformset_factory(model, request, form=ModelForm, formset=BaseGenericInlineFormSet,
                                       ct_field="content_type", fk_field="object_id", fields=None, exclude=None,
                                       extra=3, can_order=False, can_delete=True, min_num=None, max_num=None,
                                       formfield_callback=None, formreadonlyfield_callback=None, readonly_fields=None,
                                       readonly=False, validate_max=False, for_concrete_model=True):
    """
    Returns a ``GenericInlineFormSet`` for the given kwargs.

    You must provide ``ct_field`` and ``fk_field`` if they are different from
    the defaults ``content_type`` and ``object_id`` respectively.
    """
    opts = model._meta
    # if there is no field called `ct_field` let the exception propagate
    ct_field = opts.get_field(ct_field)
    if not isinstance(ct_field, models.ForeignKey) or ct_field.related_model != ContentType:
        raise Exception("fk_name '%s' is not a ForeignKey to ContentType" % ct_field)
    fk_field = opts.get_field(fk_field)  # let the exception propagate
    if exclude is not None:
        exclude = list(exclude)
        exclude.extend([ct_field.name, fk_field.name])
    else:
        exclude = [ct_field.name, fk_field.name]

    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
        'min_num': min_num,
        'validate_max': validate_max,
        'formreadonlyfield_callback': formreadonlyfield_callback,
        'readonly_fields': readonly_fields,
        'readonly': readonly,
    }

    FormSet = smartmodelformset_factory(model, request, **kwargs)
    FormSet.ct_field = ct_field
    FormSet.ct_fk_field = fk_field
    FormSet.for_concrete_model = for_concrete_model
    return FormSet
