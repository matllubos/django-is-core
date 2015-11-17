from __future__ import unicode_literals

import warnings
import itertools

from django import forms
from django.forms import models
from django.forms.fields import ChoiceField
from django.forms.models import ModelForm, ModelFormMetaclass, _get_foreign_key, BaseModelFormSet
from django.utils import six

from piston.forms import RESTModelForm

from is_core.forms import widgets
from is_core.utils.models import get_model_field_value
from is_core.forms.formsets import BaseFormSetMixin, smartformset_factory
from is_core.forms.forms import SmartFormMixin
from is_core.utils import field_humanized_value


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

    def post_save_form(self, form):
        pass

    def post_save(self):
        pass

    def set_post_save(self, commit):
        if commit:
            self.post_save()
        else:
            self.old_save_m2m = self.save_m2m
            def post_save_m2m():
                self.old_save_m2m()
                for form in self.saved_forms:
                    self.post_save_form(form)
                self.post_save()
            self.save_m2m = post_save_m2m

    def save(self, commit=True):
        obj = super(BaseInlineFormSet, self).save(commit)
        self.set_post_save(commit)
        return obj


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


class SmartModelFormMetaclass(ModelFormMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = super(SmartModelFormMetaclass, cls).__new__(cls, name, bases, attrs)

        base_readonly_fields = set(getattr(new_class, 'base_readonly_fields', ()))
        base_required_fields = set(getattr(new_class, 'base_required_fields', ()))

        opts = getattr(new_class, 'Meta', None)
        if opts:
            exclude_fields = getattr(opts, 'exclude', None) or ()
            readonly_fields = getattr(opts, 'readonly_fields', None) or ()
            readonly = getattr(opts, 'readonly', None) or False
            all_fields = getattr(opts, 'all_fields', None) or ()
            has_all_fields = hasattr(opts, 'all_fields')
            required_fields = getattr(opts, 'required_fields', None) or ()

            for field_name, field in new_class.base_fields.items():
                if field_name in exclude_fields:
                    del new_class.base_fields[field_name]
                elif ((field_name in readonly_fields or readonly or field.is_readonly) and
                      field_name not in base_readonly_fields):
                    base_readonly_fields.add(field_name)
                elif field_name in required_fields and field_name not in base_required_fields:
                    base_required_fields.add(field_name)

            for rel_object in opts.model._meta.related_objects:
                accessor_name = rel_object.get_accessor_name()
                if accessor_name in all_fields and rel_object.field.null:
                    related_model = rel_object.related_model
                    new_class.base_fields[accessor_name] = ModelMultipleChoiceField(
                        label=related_model._meta.verbose_name_plural,
                        queryset=related_model.objects.all(), required=False
                    )

            if has_all_fields:
                test_readonly_fields = all_fields
            else:
                test_readonly_fields = readonly_fields

            for field_name in test_readonly_fields:
                if (field_name not in new_class.base_fields and 'formreadonlyfield_callback' in attrs and
                    attrs['formreadonlyfield_callback'] is not None):
                    new_class.base_fields[field_name] = attrs['formreadonlyfield_callback'](field_name)
                    base_readonly_fields.add(field_name)

        new_class.base_readonly_fields = base_readonly_fields
        new_class.base_required_fields = base_required_fields
        return new_class


def humanized_model_to_dict(instance, readonly_fields, fields=None, exclude=None):
    """
    Returns a dict containing the humanized data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    opts = instance._meta
    data = {}
    for f in itertools.chain(opts.concrete_fields, opts.virtual_fields, opts.many_to_many):
        if not getattr(f, 'editable', False):
            continue
        if fields and not f.name in fields:
            continue
        if f.name not in readonly_fields:
            continue
        if exclude and f.name in exclude:
            continue

        humanized_value = field_humanized_value(instance, f)
        if humanized_value:
            data[f.name] = humanized_value
    return data


class SmartModelForm(six.with_metaclass(SmartModelFormMetaclass, SmartFormMixin, RESTModelForm)):

    def __init__(self, *args, **kwargs):
        # Set values must be ommited
        readonly_exclude = kwargs.get('initials', {}).keys()

        super(SmartModelForm, self).__init__(*args, **kwargs)

        opts = self._meta
        self.humanized_data = humanized_model_to_dict(self.instance, self.base_readonly_fields, opts.fields,
                                                      itertools.chain(opts.exclude or (), readonly_exclude or  ()))

        if self.instance.pk:
            for rel_object in opts.model._meta.related_objects:
                accessor_name = rel_object.get_accessor_name()
                if accessor_name in self.fields and accessor_name not in self.initial:
                    self.initial[accessor_name] = list(
                        getattr(self.instance, accessor_name).values_list('pk', flat=True)
                    )

    def _get_validation_exclusions(self):
        exclude = super(SmartModelForm, self)._get_validation_exclusions()
        for f in self.instance._meta.fields:
            field = f.name
            if field in self.base_readonly_fields and field not in exclude:
                exclude.append(field)
        return exclude

    def save_rel(self):
        opts = self._meta
        for rel_object in opts.model._meta.related_objects:
            accessor_name = rel_object.get_accessor_name()
            if accessor_name in self.fields:
                pks = [rel_inst.pk for rel_inst in self.cleaned_data[accessor_name]]
                prev_pks = set(getattr(self.instance, accessor_name).values_list('pk', flat=True))

                for rem_rel_inst in getattr(self.instance, accessor_name).exclude(pk__in=pks):
                    setattr(rem_rel_inst, rel_object.field.name, None)
                    rem_rel_inst.save()

                for rel_inst in self.cleaned_data[accessor_name]:
                    if rel_inst.pk not in prev_pks:
                        setattr(rel_inst, rel_object.field.name, self.instance)
                        rel_inst.save()

    def post_save(self):
        pass

    def set_post_save(self, commit):
        if commit:
            self.post_save()
        else:
            self.old_save_m2m = self.save_m2m
            def post_save_m2m():
                self.old_save_m2m()
                self.save_rel()
                self.post_save()
            self.save_m2m = post_save_m2m

    def save(self, commit=True):
        obj = super(SmartModelForm, self).save(commit)
        self.set_post_save(commit)
        return obj


def get_model_fields(model, fields):
    model_fields = []
    for field in model._meta.fields + model._meta.many_to_many:
        if field.editable and (fields is None or field.name in fields):
            model_fields.append(field.name)
    return model_fields


def smartmodelform_factory(model, request, form=SmartModelForm, fields=None, readonly_fields=None, exclude=None,
                           formfield_callback=None, widgets=None, localized_fields=None, required_fields=None,
                           labels=None, help_texts=None, error_messages=None, formreadonlyfield_callback=None,
                           readonly=False):
    attrs = {'model': model}
    if fields is not None:
        model_fields = get_model_fields(model, fields)
        attrs['all_fields'] = fields
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
    if required_fields is not None:
        attrs['required_fields'] = required_fields
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
    return form_class


def smartmodelformset_factory(model, request, form=ModelForm, formfield_callback=None,
                              formset=BaseModelFormSet, extra=1, can_delete=False,
                              can_order=False, min_num=None, max_num=None, fields=None, exclude=None,
                              widgets=None, validate_min=False, validate_max=False, localized_fields=None,
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
        validate_min=validate_min, validate_max=validate_max
    )
    FormSet.model = model
    return FormSet


def smartinlineformset_factory(parent_model, model, request, form=ModelForm,
                               formset=BaseInlineFormSet, fk_name=None,
                               fields=None, exclude=None, extra=3, can_order=False,
                               can_delete=True, min_num=None, max_num=None, formfield_callback=None,
                               widgets=None, validate_min=False, validate_max=False, localized_fields=None,
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
        'validate_min': validate_min,
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
