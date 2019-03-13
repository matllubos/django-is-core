from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelForm
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet as OriginBaseGenericInlineFormSet

from is_core.forms.models import smartmodelformset_factory
from is_core.forms.formsets import BaseFormSetMixin


class BaseGenericInlineFormSet(BaseFormSetMixin, OriginBaseGenericInlineFormSet):
    pass


def smart_generic_inlineformset_factory(model, request, form=ModelForm, formset=BaseGenericInlineFormSet,
                                        ct_field='content_type', fk_field='object_id', fields=None, exclude=None,
                                        extra=3, can_order=False, can_delete=True, min_num=None, max_num=None,
                                        formfield_callback=None, widgets=None, validate_min=False, validate_max=False,
                                        localized_fields=None, labels=None, help_texts=None, error_messages=None,
                                        formreadonlyfield_callback=None, readonly_fields=None, for_concrete_model=True,
                                        readonly=False):
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
        'widgets': widgets,
        'validate_min': validate_min,
        'validate_max': validate_max,
        'localized_fields': localized_fields,
        'formreadonlyfield_callback': formreadonlyfield_callback,
        'readonly_fields': readonly_fields,
        'readonly': readonly,
        'labels': labels,
        'help_texts': help_texts,
        'error_messages': error_messages,
    }

    FormSet = smartmodelformset_factory(model, request, **kwargs)
    FormSet.ct_field = ct_field
    FormSet.ct_fk_field = fk_field
    FormSet.for_concrete_model = for_concrete_model
    return FormSet
