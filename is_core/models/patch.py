from __future__ import unicode_literals

import six

import django.db.models.options as options

from django.db import models
from django.db.models.fields import Field, URLField
from django.db.models.fields.related import ForeignKey, ManyToManyField,  ForeignObjectRel
from django.utils.translation import ugettext_lazy as _

from chamber.patch import Options

from .humanize import url_humanized


options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_fk_filter', 'default_m2m_filter', 'default_rel_filter')


class UIOptions(Options):

    model_class = models.Model
    meta_class_name = 'UIMeta'
    meta_name = '_ui_meta'
    attributes = {
        'extra_selecbox_fields': {},
        'list_verbose_name': '%(verbose_name_plural)s',
        'add_verbose_name': _('add %(verbose_name)s'),
        'add_button_verbose_name': _('add %(verbose_name)s'),
        'add_inline_button_verbose_name': _('add %(verbose_name)s'),
        'edit_verbose_name': '%(obj)s',
        'filter_placeholders': {},
        'placeholders': {},
        'default_ui_filter_by': None,
    }


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


def field_init(self, *args, **kwargs):
    _filter = kwargs.pop('filter', None)
    if _filter:
        self._filter = _filter
    self._init_is_core_tmp(*args, **kwargs)


def rel_field_init(self, *args, **kwargs):
    self.reverse_verbose_name = kwargs.pop('reverse_verbose_name', None)
    self._rel_init_is_core_tmp(*args, **kwargs)


def field_get_filter_class(self):
    return self._filter if hasattr(self, '_filter') else self.default_filter


def fk_get_filter_class(self):
    return (
        self._filter if hasattr(self, '_filter')
        else getattr(self.rel.to._meta, 'default_fk_filter', None) or self.default_filter
    )


def m2m_get_filter_class(self):
    return (
        self._filter if hasattr(self, '_filter')
        else getattr(self.rel.to._meta, 'default_m2m_filter', None) or self.default_filter
    )


def rel_get_filter_class(self):
    return getattr(self.field.model._meta, 'default_rel_filter', None) or self.default_filter


Field._init_is_core_tmp = Field.__init__
Field.__init__ = field_init
Field.filter = property(field_get_filter_class)

ForeignKey.formfield = fk_formfield
ForeignKey._rel_init_is_core_tmp = ForeignKey.__init__
ForeignKey.__init__ = rel_field_init
ForeignKey.filter = property(fk_get_filter_class)

ManyToManyField.formfield = m2m_formfield
ManyToManyField._rel_init_is_core_tmp = ManyToManyField.__init__
ManyToManyField.__init__ = rel_field_init
ManyToManyField.filter = property(m2m_get_filter_class)

ForeignObjectRel.filter = property(rel_get_filter_class)

URLField.default_humanized = url_humanized

# because it is not translated in Django
_('(None)')
