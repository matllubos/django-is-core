from django.forms.models import inlineformset_factory, ModelForm

from is_core.forms.models import BaseInlineFormSet
from is_core.utils.forms import formset_has_file_field


class InlineFormView(object):
    form_class = ModelForm
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
    base_inline_formset_class = BaseInlineFormSet

    def __init__(self, request, parent_view, instance, is_readonly=False):
        self.request = request
        self.parent_view = parent_view
        self.parent_model = parent_view.model
        self.core = parent_view.core
        self.parent = instance
        self.is_readonly = is_readonly
        if self.extra < self.min_num:
            self.extra = self.min_num

        self.formset = self.get_formset(instance, self.request.POST, self.request.FILES)

        for i in range(self.min_num):
            self.formset.forms[i].empty_permitted = False

    def get_exclude(self):
        return self.exclude

    def get_fields(self):
        return self.fields

    def get_extra(self):
        return self.extra

    def get_can_delete(self):
        return self.can_delete and not self.is_readonly

    def get_can_add(self):
        return self.can_add and not self.is_readonly

    def get_readonly_fields(self):
        if self.is_readonly:
            return self.get_formset_factory().form.base_fields.keys()

        return self.readonly_fields

    def get_fieldset(self, formset):
        fields = self.get_fields() or formset.form.base_fields.keys()
        fields = list(fields) + list(self.get_readonly_fields())
        if self.get_can_delete():
            fields.append('DELETE')
        return fields

    def get_formset_factory(self, fields=None, readonly_fields=()):
        extra = self.get_extra()
        exclude = list(self.get_exclude()) + list(readonly_fields)
        return inlineformset_factory(self.parent_model, self.model, form=self.form_class,
                                     fk_name=self.fk_name, extra=extra, formset=self.base_inline_formset_class,
                                     can_delete=self.get_can_delete(), exclude=exclude,
                                     fields=fields, max_num=self.max_num)

    def get_queryset(self):
        return self.model.objects.all()

    def get_formset(self, instance, data, files):
        fields = self.get_fields()
        readonly_fields = self.get_readonly_fields()

        if data:
            formset = self.get_formset_factory(fields, readonly_fields)(data=data, files=files, instance=instance,
                                                                        queryset=self.get_queryset())
        else:
            formset = self.get_formset_factory(fields, readonly_fields)(instance=instance, queryset=self.get_queryset())

        formset.can_add = self.get_can_add()
        formset.can_delete = self.get_can_delete()

        for form in formset:
            form.class_names = self.form_class_names(form)
            self.form_fields(form)
        return formset

    def form_class_names(self, form):
        if form.instance.pk:
            return ['empty']
        return []

    def form_fields(self, form):
        for field_name, field in form.fields.items():
            field = self.form_field(form, field_name, field)

    def form_field(self, form, field_name, form_field):
        return form_field

    def get_name(self):
        return self.model.__name__

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
