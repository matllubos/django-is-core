from __future__ import unicode_literals

import six

from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.utils.translation import ugettext_lazy as _


class OptionsLazy(object):

    def __init__(self, name, klass):
        self.name = name
        self.klass = klass

    def __get__(self, instance=None, owner=None):
        option = self.klass(owner)
        setattr(owner, self.name, option)
        return option


class Options(object):

    def __init__(self, model):
        self.model = model


class UIOptions(Options):

    def __init__(self, model):
        super(UIOptions, self).__init__(model)
        self.extra_selecbox_fields = {}
        self.list_verbose_name = _('%(verbose_name_plural)s')
        self.add_verbose_name = _('Add %(verbose_name)s')
        self.edit_verbose_name = _('%(obj)s')
        self.filter_placeholders = {}
        self.placeholders = {}

        if hasattr(model, 'UIMeta'):
            self.extra_selecbox_fields = getattr(model.UIMeta, 'extra_selecbox_fields', self.extra_selecbox_fields)
            self.list_verbose_name = getattr(model.UIMeta, 'list_verbose_name', self.list_verbose_name)
            self.add_verbose_name = getattr(model.UIMeta, 'add_verbose_name', self.add_verbose_name)
            self.edit_verbose_name = getattr(model.UIMeta, 'edit_verbose_name', self.edit_verbose_name)
            self.filter_placeholders = getattr(model.UIMeta, 'filter_placeholders', self.filter_placeholders)
            self.placeholders = getattr(model.UIMeta, 'placeholders', self.placeholders)


class RestOptions(Options):

    def __init__(self, model):
        from piston.utils import model_default_rest_fields

        self.fields = model_default_rest_fields(model)

        if hasattr(model, 'RestMeta'):
            self.fields = getattr(model.RestMeta, 'fields', self.fields)
            self.default_list_fields = getattr(model.RestMeta, 'default_list_fields' , self.fields)
            self.default_obj_fields = getattr(model.RestMeta, 'default_obj_fields', self.fields)
        else:
            self.default_list_fields = self.fields
            self.default_obj_fields = self.fields

        self.fields = set(self.fields)
        self.default_list_fields = set(self.default_list_fields)
        self.default_obj_fields = set(self.default_obj_fields)


OPTIONS = {'_rest_meta': RestOptions, '_ui_meta': UIOptions}

for opt_key, opt_class in OPTIONS.items():
    setattr(models.Model, opt_key, OptionsLazy(opt_key, opt_class))


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
