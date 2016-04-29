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

    meta_name = None

    def __init__(self, model):
        self.model = model

    def _getattr(self, name, default_value):
        meta_models = [b for b in self.model.__mro__ if issubclass(b, models.Model)]
        for model in meta_models:
            meta = getattr(model, self.meta_name, None)
            if meta:
                value = getattr(meta, name, None)
                if value is not None:
                    return value
        return default_value


class UIOptions(Options):

    meta_name = 'UIMeta'

    def __init__(self, model):
        super(UIOptions, self).__init__(model)
        self.extra_selecbox_fields = {}
        self.list_verbose_name = '%(verbose_name_plural)s'
        self.add_verbose_name = _('add %(verbose_name)s')
        self.add_button_verbose_name = self.add_verbose_name
        self.add_inline_button_verbose_name = self.add_verbose_name
        self.edit_verbose_name = '%(obj)s'
        self.filter_placeholders = {}
        self.placeholders = {}

        if hasattr(model, 'UIMeta'):
            self.extra_selecbox_fields = self._getattr('extra_selecbox_fields', self.extra_selecbox_fields)
            self.list_verbose_name = self._getattr('list_verbose_name', self.list_verbose_name)
            self.add_verbose_name = self._getattr('add_verbose_name', self.add_verbose_name)
            self.add_button_verbose_name = self._getattr('add_button_verbose_name', self.add_verbose_name)
            self.add_inline_button_verbose_name = self._getattr('add_inline_button_verbose_name', self.add_verbose_name)
            self.edit_verbose_name = self._getattr('edit_verbose_name', self.edit_verbose_name)
            self.filter_placeholders = self._getattr('filter_placeholders', self.filter_placeholders)
            self.placeholders = self._getattr('placeholders', self.placeholders)


class RESTOptions(Options):

    meta_name = 'RESTMeta'

    def __init__(self, model):
        super(RESTOptions, self).__init__(model)
        from piston.utils import model_default_rest_fields

        self.default_general_fields = set(self._getattr('default_general_fields' , ('id', '_obj_name', '_rest_links')))
        self.default_detailed_fields = set(self._getattr('default_detailed_fields', model_default_rest_fields(model)))
        self.extra_fields = set(self._getattr('extra_fields', ()))
        self.guest_fields = set(self._getattr('guest_fields' , ('id', '_obj_name')))


OPTIONS = {'_rest_meta': RESTOptions, '_ui_meta': UIOptions}

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


# because it is not translated in Django
_('(None)')
