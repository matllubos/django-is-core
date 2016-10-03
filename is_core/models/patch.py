from __future__ import unicode_literals

import six

from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.utils.translation import ugettext_lazy as _

from chamber.patch import Options, OptionsLazy


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


ForeignKey.formfield = fk_formfield
ManyToManyField.formfield = m2m_formfield


# because it is not translated in Django
_('(None)')
