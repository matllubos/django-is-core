from __future__ import unicode_literals

from django import forms
from django.forms import models
from django.forms.fields import ChoiceField

from is_core.forms import widgets
from is_core.utils.models import get_model_field_value
from is_core.forms.formsets import BaseFormSetMixin


class BaseInlineFormSet(BaseFormSetMixin, models.BaseInlineFormSet):

    def save_existing_objects(self, commit=True):
        self.changed_objects = []
        self.deleted_objects = []
        if not self.initial_forms:
            return []

        saved_instances = []
        forms_to_delete = self.deleted_forms
        for form in self.initial_forms:
            pk_name = self._pk_field.name
            raw_pk_value = form._raw_value(pk_name)

            # clean() for different types of PK fields can sometimes return
            # the model instance, and sometimes the PK. Handle either.
            pk_value = form.fields[pk_name].clean(raw_pk_value)
            pk_value = getattr(pk_value, 'pk', pk_value)

            obj = self._existing_object(pk_value)
            if form in forms_to_delete:
                self.deleted_objects.append(obj)
                if commit:
                    obj.delete()
                continue
            if form.has_changed():
                self.changed_objects.append((obj, form.changed_data))
                saved_instances.append(self.save_existing(form, obj, commit=commit))
                if not commit:
                    self.saved_forms.append(form)
        return saved_instances


class ModelChoice(list):

    def __init__(self, id, label, attrs={}):
        self.append(id)
        self.append(label)
        self.attrs = attrs


class ModelChoiceIterator(forms.models.ModelChoiceIterator):

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ModelChoice("", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for obj in self.queryset.all():
                yield self.choice(obj)

    def choice(self, obj):
        attrs = {}
        for key, val in obj._ui_meta.extra_selecbox_fields.items():
            attrs[key] = get_model_field_value(val, obj)
        return ModelChoice(self.field.prepare_value(obj), self.field.label_from_instance(obj), attrs)


class ModelChoiceFieldMixin(object):

    widget = widgets.Select

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return ModelChoiceIterator(self)
    choices = property(_get_choices, ChoiceField._set_choices)


class ModelChoiceField(ModelChoiceFieldMixin, forms.ModelChoiceField):

    widget = widgets.Select


class ModelMultipleChoiceField(ModelChoiceFieldMixin, forms.ModelMultipleChoiceField):

    widget = widgets.MultipleSelect
