import django.db.models.options as options

from django.db import models
from django.db.models.fields import Field, URLField
from django.db.models.fields.related import ForeignKey, ManyToManyField, ForeignObjectRel, OneToOneField
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
        'detail_verbose_name': '%(obj)s',
        'filter_placeholders': {},
        'placeholders': {},
        'default_ui_filter_by': None,
    }


def fk_formfield(self, **kwargs):
    from is_core import forms as is_forms

    kwargs.setdefault('form_class', is_forms.ModelChoiceField)
    return self._is_core_formfield_tmp(**kwargs)


def m2m_formfield(self, **kwargs):
    from is_core import forms as is_forms

    kwargs.setdefault('form_class', is_forms.ModelMultipleChoiceField,)
    return self._is_core_formfield_tmp(**kwargs)


def rel_field_init(self, *args, **kwargs):
    self._reverse_verbose_name = kwargs.pop('reverse_verbose_name', None)
    self._is_core_init_tmp(*args, **kwargs)


def get_reverse_verbose_name_plural(self):
    return self._reverse_verbose_name or self.model._meta.verbose_name_plural


def get_reverse_verbose_name(self):
    return self._reverse_verbose_name or self.model._meta.verbose_name


ForeignKey._is_core_formfield_tmp = ForeignKey.formfield
ForeignKey.formfield = fk_formfield
ForeignKey._is_core_init_tmp = ForeignKey.__init__
ForeignKey.__init__ = rel_field_init
ForeignKey.reverse_verbose_name = property(get_reverse_verbose_name_plural)

OneToOneField.reverse_verbose_name = property(get_reverse_verbose_name)

ManyToManyField._is_core_formfield_tmp = ManyToManyField.formfield
ManyToManyField.formfield = m2m_formfield
ManyToManyField._is_core_init_tmp = ManyToManyField.__init__
ManyToManyField.__init__ = rel_field_init
ManyToManyField.reverse_verbose_name = property(get_reverse_verbose_name_plural)

URLField.default_humanized = url_humanized
