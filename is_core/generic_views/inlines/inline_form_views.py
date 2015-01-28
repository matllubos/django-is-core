from __future__ import unicode_literals

from django.db import models

from chamber.utils.forms import formset_has_file_field

from is_core.forms.models import BaseInlineFormSet, smartinlineformset_factory, SmartModelForm
from is_core.generic_views.inlines import InlineView
from is_core.utils import get_field_value_and_label
from is_core.forms.fields import SmartReadonlyField
from is_core.forms.widgets import ModelChoiceReadonlyWidget


class InlineFormView(InlineView):
    form_class = SmartModelForm
    model = None
    fk_name = None
    template_name = None
    extra = 0
    exclude = ()
    can_add = True
    can_delete = True
    max_num = None
    min_num = 0
    readonly_fields = ()
    fields = None
    initial = []
    base_inline_formset_class = BaseInlineFormSet

    def __init__(self, request, parent_view, parent_instance):
        super(InlineFormView, self).__init__(request, parent_view, parent_instance)
        self.parent_model = parent_view.model
        self.core = parent_view.core
        self.parent_instance = parent_instance
        self.readonly = self.is_readonly()
        self.formset = self.get_formset(parent_instance, self.request.POST, self.request.FILES)

        for i in range(self.min_num):
            self.formset.forms[i].empty_permitted = False

    def is_readonly(self):
        return not self.parent_view.has_post_permission(obj=self.parent_view.get_obj())

    def get_context_data(self, **kwargs):
        context_data = super(InlineFormView, self).get_context_data(**kwargs)
        formset = self.formset
        fieldset = self.get_fieldset(formset)
        class_names = [self.get_name().lower()]
        if formset.can_add:
            class_names.append('can-add')
        if formset.can_delete:
            class_names.append('can-delete')

        if kwargs.get('title'):
            class_names.append('with-title')
        else:
            class_names.append('without-title')

        context_data.update({
            'formset': formset,
            'fieldset': fieldset,
            'name': self.get_name(),
            'button_value': self.get_button_value(),
            'class_names': class_names,
        })
        return context_data

    def get_exclude(self):
        return self.exclude

    def get_fields(self):
        return self.fields

    def get_extra(self):
        return self.extra + len(self.get_initial())

    def get_initial(self):
        return self.initial[:]

    def get_can_delete(self):
        return self.can_delete and not self.readonly

    def get_can_add(self):
        return self.can_add and not self.readonly

    def get_readonly_fields(self):
        return self.readonly_fields

    def get_prefix(self):
        return '-'.join((self.parent_view.get_prefix(), 'inline', self.__class__.__name__)).lower()

    def get_fieldset(self, formset):
        fields = list(self.get_fields() or formset.form.base_fields.keys())
        if self.get_can_delete():
            fields.append('DELETE')
        return fields

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = db_field.formfield(**kwargs)
        if isinstance(db_field, (models.ForeignKey, models.OneToOneField)):
            field.readonly_widget = ModelChoiceReadonlyWidget
        return field

    def formfield_for_readonlyfield(self, name, **kwargs):
        def get_val_and_label_fun(instance):
            return get_field_value_and_label(name, (self, self.core, instance),
                                                     {'request':self.request}, self.request)
        return SmartReadonlyField(get_val_and_label_fun)

    def get_formset_factory(self, fields=None, readonly_fields=()):
        extra = self.get_extra()
        exclude = self.get_exclude()
        return smartinlineformset_factory(
            self.parent_model, self.model, self.request, form=self.form_class, fk_name=self.fk_name, extra=extra,
            formset=self.base_inline_formset_class, can_delete=self.get_can_delete(), exclude=exclude,
            fields=fields, formfield_callback=self.formfield_for_dbfield, min_num=self.min_num, max_num=self.max_num,
            readonly_fields=readonly_fields, readonly=self.readonly, formreadonlyfield_callback=self.formfield_for_readonlyfield
        )

    def get_queryset(self):
        return self.model.objects.all()

    def get_formset(self, instance, data, files):
        fields = self.get_fields()
        readonly_fields = self.get_readonly_fields()

        if data:
            formset = self.get_formset_factory(fields, readonly_fields)(data=data, files=files, instance=instance,
                                                                        queryset=self.get_queryset(),
                                                                        prefix=self.get_prefix())
        else:
            formset = self.get_formset_factory(fields, readonly_fields)(instance=instance,
                                                                        queryset=self.get_queryset(),
                                                                        initial=self.get_initial(),
                                                                        prefix=self.get_prefix())

        formset.can_add = self.get_can_add()
        formset.can_delete = self.get_can_delete()

        for form in formset:
            form.class_names = self.form_class_names(form)
            self.form_fields(form)
        return formset

    def form_class_names(self, form):
        if not form.instance.pk:
            return ['empty']
        return []

    def form_fields(self, form):
        for field_name, field in form.fields.items():
            field = self.form_field(form, field_name, field)

    def form_field(self, form, field_name, form_field):
        placeholder = self.model._ui_meta.placeholders.get('field_name', None)
        if placeholder:
            form_field.widget.placeholder = self.model._ui_meta.placeholders.get('field_name', None)
        return form_field

    def get_name(self):
        return self.model.__name__

    def get_button_value(self):
        return (self.model._ui_meta.add_inline_button_verbose_name % {
            'verbose_name': self.model._meta.verbose_name,
            'verbose_name_plural': self.model._meta.verbose_name_plural
        })

    def form_valid(self, request):
        instances = self.formset.save(commit=False)
        for obj in instances:
            change = obj.pk is not None
            self.save_obj(obj, change)
        for obj in self.formset.deleted_objects:
            self.delete_obj(obj)

    def get_has_file_field(self):
        return formset_has_file_field(self.formset.form)

    def pre_save_obj(self, obj, change):
        pass

    def post_save_obj(self, obj, change):
        pass

    def save_obj(self, obj, change):
        self.pre_save_obj(obj, change)
        obj.save()
        self.post_save_obj(obj, change)

    def pre_delete_obj(self, obj):
        pass

    def post_delete_obj(self, obj):
        pass

    def delete_obj(self, obj):
        self.pre_delete_obj(obj)
        obj.delete()
        self.post_delete_obj(obj)


class TabularInlineFormView(InlineFormView):
    template_name = 'forms/tabular_inline_formset.html'


class StackedInlineFormView(InlineFormView):
    template_name = 'forms/stacked_inline_formset.html'


class ResponsiveInlineFormView(InlineFormView):
    template_name = 'forms/responsive_inline_formset.html'
