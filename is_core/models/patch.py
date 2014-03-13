from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField

import six
from django.db.models.fields.files import FileField


class UIOptions(object):
    def __init__(self, model):
        self.extra_selecbox_fields = {}

        if hasattr(model, 'UIMeta'):
            self.extra_selecbox_fields = getattr(model.UIMeta, 'extra_selecbox_fields', self.extra_selecbox_fields)


class RestOptions(object):
    def __init__(self, model):
        from is_core.rest.utils import model_default_rest_fields

        self.fields = model_default_rest_fields(model)
        self.default_list_fields = self.fields
        self.default_obj_fields = self.fields

        if hasattr(model, 'RestMeta'):
            self.fields = getattr(model.RestMeta, 'fields', self.fields)
            self.default_list_fields = getattr(model.RestMeta, 'default_list_fields' , self.default_list_fields)
            self.default_obj_fields = getattr(model.RestMeta, 'default_obj_fields', self.default_obj_fields)

        self.fields = set(self.fields)
        self.default_list_fields = set(self.default_list_fields)
        self.default_obj_fields = set(self.default_obj_fields)


for model_cls in models.get_models():
    model_cls._rest_meta = RestOptions(model_cls)
    model_cls._ui_meta = UIOptions(model_cls)


def fk_formfield(self, **kwargs):
    from is_core import forms as is_forms

    db = kwargs.pop('using', None)
    if isinstance(self.rel.to, six.string_types):
        raise ValueError("Cannot create form field for %r yet, because "
                         "its related model %r has not been loaded yet" %
                         (self.name, self.rel.to))
    defaults = {
        'form_class': is_forms.ModelChoiceField,
        'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to),
        'to_field_name': self.rel.field_name,
    }
    defaults.update(kwargs)
    return super(ForeignKey, self).formfield(**defaults)


def m2m_formfield(self, **kwargs):
    from is_core import forms as is_forms

    db = kwargs.pop('using', None)
    defaults = {
        'form_class': is_forms.ModelMultipleChoiceField,
        'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to)
    }
    defaults.update(kwargs)
    # If initial is passed in, it's a list of related objects, but the
    # MultipleChoiceField takes a list of IDs.
    if defaults.get('initial') is not None:
        initial = defaults['initial']
        if callable(initial):
            initial = initial()
        defaults['initial'] = [i._get_pk_val() for i in initial]
    return super(ManyToManyField, self).formfield(**defaults)


ForeignKey.formfield = fk_formfield
ManyToManyField.formfield = m2m_formfield