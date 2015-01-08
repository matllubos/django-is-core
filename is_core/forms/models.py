from __future__ import unicode_literals

import warnings

from django import forms
from django.forms import models
from django.forms.fields import ChoiceField, FileField
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm, ModelFormMetaclass, _get_foreign_key, BaseModelFormSet
from django.utils import six
from django.forms.formsets import DEFAULT_MAX_NUM, BaseFormSet as OriginBaseFormSet

from piston.forms import RestModelForm

from is_core.forms import widgets
from is_core.utils.models import get_model_field_value
from is_core.forms.formsets import BaseFormSetMixin
from is_core.forms.forms import ReadonlyBoundField, SmartBoundField


class BaseFormSet(BaseFormSetMixin, OriginBaseFormSet):
    pass


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

    def __init__(self, id, label, obj=None, attrs={}):
        self.append(id)
        self.append(label)
        self.attrs = attrs
        self.obj = obj


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
        return ModelChoice(self.field.prepare_value(obj), self.field.label_from_instance(obj), obj, attrs)


class ModelChoiceFieldMixin(object):

    widget = widgets.Select

    def __init__(self, queryset, *args, **kwargs):
        self.model = queryset.model
        super(ModelChoiceFieldMixin, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return ModelChoiceIterator(self)
    choices = property(_get_choices, ChoiceField._set_choices)

    def widget_attrs(self, widget):
        attrs = super(ModelChoiceFieldMixin, self).widget_attrs(widget)
        options = self.model._meta
        attrs['data-model'] = '%s.%s' % (options.app_label, options.object_name)
        return attrs


class ModelChoiceField(ModelChoiceFieldMixin, forms.ModelChoiceField):

    widget = widgets.Select


class ModelMultipleChoiceField(ModelChoiceFieldMixin, forms.ModelMultipleChoiceField):

    widget = widgets.MultipleSelect


class SmartFormMetaclass(ModelFormMetaclass):

    def __new__(cls, name, bases,
                attrs):
        new_class = super(SmartFormMetaclass, cls).__new__(cls, name, bases,
                attrs)

        opts = getattr(new_class, 'Meta', None)
        if opts:
            exclude_fields = getattr(opts, 'exclude', None) or ()
            non_model_fields = getattr(opts, 'non_model_fields', None) or ()
            readonly_fields = getattr(opts, 'readonly_fields', None) or ()
            readonly = getattr(opts, 'readonly', None) or False
            fields = getattr(opts, 'fields', None) or ()

            base_readonly_fields = []
            for name, field in new_class.base_fields.items():
                if name in exclude_fields:
                    del new_class.base_fields[name]
                elif name in readonly_fields or readonly or field.is_readonly:
                    base_readonly_fields.append(name)

            for field_name in set(fields).union(set(readonly_fields)).union(set(non_model_fields)):
                if field_name not in new_class.base_fields and 'formreadonlyfield_callback' in attrs:
                    new_class.base_fields[field_name] = attrs['formreadonlyfield_callback'](field_name)
                    base_readonly_fields.append(field_name)

            new_class.base_readonly_fields = base_readonly_fields
        return new_class


class SmartFormMixin(six.with_metaclass(SmartFormMetaclass, object)):

    def __init__(self, *args, **kwargs):
        super(SmartFormMixin, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(self, '_init_%s' % field_name):
                getattr(self, '_init_%s' % field_name)(field)
        self._init_fields()

    def _init_fields(self):
        pass

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)

        if name in self.base_readonly_fields:
            return ReadonlyBoundField(self, field, name)
        else:
            return SmartBoundField(self, field, name)

    def _get_readonly_widget(self, field_name, field, widget):
        if field.readonly_widget:
            return field.readonly_widget(widget)
        return field.widget

    def _clean_fields(self):
        for name, field in self.fields.items():
            if name not in self.base_readonly_fields:
                # value_from_datadict() gets the data from the data dictionaries.
                # Each widget type knows how to retrieve its own data, because some
                # widgets split data over several HTML fields.
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                try:
                    if isinstance(field, FileField):
                        initial = self.initial.get(name, field.initial)
                        value = field.clean(value, initial)
                    else:
                        value = field.clean(value)
                    self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
                except ValidationError as e:
                    self._errors[name] = self.error_class(e.messages)
                    if name in self.cleaned_data:
                        del self.cleaned_data[name]

    def _set_readonly(self, field_name):
        if field_name not in self.base_readonly_fields:
            self.base_readonly_fields.append(field_name)

    def post_save(self):
        pass

    def set_post_save(self, commit):
        if commit:
            self.post_save()
        else:
            self.old_save_m2m = self.save_m2m
            def post_save_m2m():
                self.old_save_m2m()
                self.post_save()
            self.save_m2m = post_save_m2m

    def save(self, commit=True):
        obj = super(SmartFormMixin, self).save(commit)
        self.set_post_save(commit)
        return obj


class SmartModelForm(SmartFormMixin, RestModelForm):
    pass


def get_model_fields(model, fields):
    model_fields = []
    for field in model._meta.fields + model._meta.many_to_many:
        if field.editable and (not fields or field.name in fields):
            model_fields.append(field.name)
    return model_fields


def smartmodelform_factory(model, request, form=SmartModelForm, fields=None, readonly_fields=None, exclude=None,
                           formfield_callback=None, widgets=None, localized_fields=None,
                           labels=None, help_texts=None, error_messages=None, formreadonlyfield_callback=None,
                           readonly=False):
    attrs = {'model': model}
    if fields is not None:
        model_fields = get_model_fields(model, fields)
        attrs['fields'] = model_fields
        attrs['non_model_fields'] = set(fields) - set(model_fields)
    if exclude is not None:
        attrs['exclude'] = exclude
    if widgets is not None:
        attrs['widgets'] = widgets
    if localized_fields is not None:
        attrs['localized_fields'] = localized_fields
    if labels is not None:
        attrs['labels'] = labels
    if help_texts is not None:
        attrs['help_texts'] = help_texts
    if error_messages is not None:
        attrs['error_messages'] = error_messages
    if readonly_fields is not None:
        attrs['readonly_fields'] = readonly_fields
    attrs['readonly'] = readonly
    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type(str('Meta'), parent, attrs)

    class_name = model.__name__ + str('Form')

    form_class_attrs = {
        'Meta': Meta,
        'formfield_callback': formfield_callback,
        'formreadonlyfield_callback': formreadonlyfield_callback,
        '_request': request,
    }

    if (getattr(Meta, 'fields', None) is None and
        getattr(Meta, 'exclude', None) is None):
        warnings.warn("Calling modelform_factory without defining 'fields' or "
                      "'exclude' explicitly is deprecated",
                      PendingDeprecationWarning, stacklevel=2)
    form_class = type(form)(class_name, (form,), form_class_attrs)
    form_class._meta.readonly_fields = readonly_fields or ()
    return form_class


def smartformset_factory(form, formset=BaseFormSet, extra=1, can_order=False,
                    can_delete=False, min_num=None, max_num=None, validate_max=False):
    """Return a FormSet for the given form class."""
    if max_num is None:
        max_num = DEFAULT_MAX_NUM
    # hard limit on forms instantiated, to prevent memory-exhaustion attacks
    # limit is simply max_num + DEFAULT_MAX_NUM (which is 2*DEFAULT_MAX_NUM
    # if max_num is None in the first place)
    absolute_max = max_num + DEFAULT_MAX_NUM
    if min_num is None:
        min_num = 0

    attrs = {'form': form, 'extra': extra,
             'can_order': can_order, 'can_delete': can_delete, 'min_num': min_num,
             'max_num': max_num, 'absolute_max': absolute_max,
             'validate_max' : validate_max}
    return type(form.__name__ + str('FormSet'), (formset,), attrs)


def smartmodelformset_factory(model, request, form=ModelForm, formfield_callback=None,
                              formset=BaseModelFormSet, extra=1, can_delete=False,
                              can_order=False, min_num=None, max_num=None, fields=None, exclude=None,
                              widgets=None, validate_max=False, localized_fields=None,
                              labels=None, help_texts=None, error_messages=None,
                              formreadonlyfield_callback=None, readonly_fields=None,
                              readonly=False):
    meta = getattr(form, 'Meta', None)
    if meta is None:
        meta = type(str('Meta'), (object,), {})
    if (getattr(meta, 'fields', fields) is None and
        getattr(meta, 'exclude', exclude) is None):
        warnings.warn("Calling modelformset_factory without defining 'fields' or "
                      "'exclude' explicitly is deprecated",
                      PendingDeprecationWarning, stacklevel=2)

    form = smartmodelform_factory(
        model, request, form=form, fields=fields, exclude=exclude, formfield_callback=formfield_callback,
        widgets=widgets, localized_fields=localized_fields, labels=labels, help_texts=help_texts,
        error_messages=error_messages, formreadonlyfield_callback=formreadonlyfield_callback,
        readonly_fields=readonly_fields, readonly=readonly
    )
    FormSet = smartformset_factory(
        form, formset, extra=extra, min_num=min_num, max_num=max_num, can_order=can_order, can_delete=can_delete,
        validate_max=validate_max
    )
    FormSet.model = model
    return FormSet


def smartinlineformset_factory(parent_model, model, request, form=ModelForm,
                               formset=BaseInlineFormSet, fk_name=None,
                               fields=None, exclude=None, extra=3, can_order=False,
                               can_delete=True, min_num=None, max_num=None, formfield_callback=None,
                               widgets=None, validate_max=False, localized_fields=None,
                               labels=None, help_texts=None, error_messages=None,
                               formreadonlyfield_callback=None, readonly_fields=None,
                               readonly=False):
    fk = _get_foreign_key(parent_model, model, fk_name=fk_name)
    # enforce a max_num=1 when the foreign key to the parent model is unique.
    if fk.unique:
        max_num = 1
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
        'validate_max': validate_max,
        'localized_fields': localized_fields,
        'labels': labels,
        'help_texts': help_texts,
        'error_messages': error_messages,
        'formreadonlyfield_callback': formreadonlyfield_callback,
        'readonly_fields': readonly_fields,
        'readonly': readonly,
    }
    FormSet = smartmodelformset_factory(model, request, **kwargs)
    FormSet.fk = fk
    return FormSet
