import warnings
import itertools

from django import forms
from django.forms import models
from django.forms.fields import ChoiceField
from django.forms.models import ModelForm, ModelFormMetaclass, _get_foreign_key, BaseModelFormSet

from pyston.forms import RESTModelForm, RESTFormMetaclass

from is_core.forms import widgets
from is_core.utils.models import get_model_field_value
from is_core.forms.formsets import BaseFormSetMixin, smartformset_factory
from is_core.forms.forms import SmartFormMixin


class BaseInlineFormSet(BaseFormSetMixin, models.BaseInlineFormSet):

    def _pre_save(self, obj):
        pass

    def _post_save_form(self, form):
        pass

    def _post_save(self, obj):
        pass

    def _set_post_save(self, commit, obj):
        if commit:
            self._post_save(obj)
        else:
            self.old_save_m2m = self.save_m2m

            def post_save_m2m():
                self.old_save_m2m()
                for form in self.saved_forms:
                    self._post_save_form(form)
                self._post_save(obj)
            self.save_m2m = post_save_m2m

    def save(self, commit=True):
        obj = super(BaseInlineFormSet, self).save(commit=False)
        self._pre_save(obj)
        if commit:
            obj.save()
        self._set_post_save(commit, obj)
        return obj


class ModelChoice(list):

    def __init__(self, id, label, obj=None, attrs={}):
        self.append(id)
        self.append(label)
        self.attrs = attrs
        self.obj = obj


class ModelChoiceIterator(forms.models.ModelChoiceIterator):

    def __iter__(self):
        return (
            ModelChoice(*choice) if not isinstance(choice, ModelChoice) else choice
            for choice in super(ModelChoiceIterator, self).__iter__()
        )

    def choice(self, obj):
        attrs = {}
        for key, val in obj._ui_meta.extra_selecbox_fields.items():
            attrs[key] = get_model_field_value(val, obj)
        return ModelChoice(self.field.prepare_value(obj), self.field.label_from_instance(obj), obj, attrs)

    def get_choice_from_value(self, value):
        try:
            obj = self.field.get_obj_from_value(value)
        except forms.ValidationError:
            return None

        if obj and self.queryset.filter(pk=obj.pk).exists():
            return self.choice(obj)
        else:
            return None


class ModelChoiceFieldMixin:

    widget = widgets.FulltextSelect

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

    def get_obj_from_value(self, value):
        raise NotImplementedError


class ModelChoiceField(ModelChoiceFieldMixin, forms.ModelChoiceField):

    widget = widgets.RestrictedSelectWidget
    readonly_widget = widgets.ModelChoiceReadonlyWidget

    def get_obj_from_value(self, value):
        return self.to_python(value)


class ModelMultipleChoiceField(ModelChoiceFieldMixin, forms.ModelMultipleChoiceField):

    widget = widgets.RestrictedSelectMultipleWidget
    readonly_widget = widgets.ModelMultipleReadonlyWidget

    def get_obj_from_value(self, value):
        return self.to_python([value])[0]


class SmartModelFormMetaclass(RESTFormMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = super(SmartModelFormMetaclass, cls).__new__(cls, name, bases, attrs)

        base_readonly_fields = set(getattr(new_class, 'base_readonly_fields', ()))
        base_required_fields = set(getattr(new_class, 'base_required_fields', ()))

        opts = getattr(new_class, 'Meta', None)
        if opts:
            setattr(opts, 'fields_to_clean', getattr(opts, 'fields_to_clean', None))
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
    for f in itertools.chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not getattr(f, 'editable', False):
            continue
        if fields and f.name not in fields:
            continue
        if f.name not in readonly_fields:
            continue
        if exclude and f.name in exclude:
            continue

        if f.humanized:
            data[f.name] = f.humanized(getattr(instance, f.name), instance)
    return data


class SmartModelForm(SmartFormMixin, RESTModelForm, metaclass=SmartModelFormMetaclass):

    def __init__(self, *args, **kwargs):
        # Set values must be omitted
        readonly_exclude = kwargs.get('initials', {}).keys()

        super(SmartModelForm, self).__init__(*args, **kwargs)

        opts = self._meta
        self.humanized_data = humanized_model_to_dict(self.instance, self.readonly_fields, opts.fields,
                                                      itertools.chain(opts.exclude or (), readonly_exclude or ()))

    def _get_validation_exclusions(self):
        exclude = super(SmartModelForm, self)._get_validation_exclusions()
        for f in self.instance._meta.fields:
            field = f.name
            if field in self.readonly_fields and field not in exclude:
                exclude.append(field)
        return exclude


def get_model_fields(model, fields):
    model_fields = []
    for field in model._meta.fields + model._meta.many_to_many:
        if field.editable and (fields is None or field.name in fields):
            model_fields.append(field.name)
    return model_fields


def smartmodelform_factory(model, request, form=SmartModelForm, fields=None, readonly_fields=None, exclude=None,
                           formfield_callback=None, widgets=None, localized_fields=None, required_fields=None,
                           labels=None, help_texts=None, error_messages=None, formreadonlyfield_callback=None,
                           readonly=False, fields_to_clean=None, is_bulk=False):
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
    if fields_to_clean is not None:
        attrs['fields_to_clean'] = fields_to_clean
    attrs['readonly'] = readonly
    attrs['is_bulk'] = is_bulk
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

    if getattr(Meta, 'fields', None) is None and getattr(Meta, 'exclude', None) is None:
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
    if getattr(meta, 'fields', fields) is None and getattr(meta, 'exclude', exclude) is None:
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
        'validate_min': validate_min,
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
