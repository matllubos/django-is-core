from django.forms.models import inlineformset_factory, ModelForm

from is_core.form.models import BaseInlineFormSet
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

    readonly_fields = ()
    fields = None

    def __init__(self, request, core, parent_model, instance, is_readonly=False):
        self.request = request
        self.parent_model = parent_model
        self.core = core
        self.parent = instance
        self.is_readonly = is_readonly
        self.formset = self.get_formset(instance, self.request.POST, self.request.FILES)

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
                                     fk_name=self.fk_name, extra=extra, formset=BaseInlineFormSet,
                                     can_delete=self.get_can_delete(), exclude=exclude,
                                     fields=fields)

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
        return formset

    def get_name(self):
        return self.model.__name__

    def form_valid(self, request):
        instances = self.formset.save(commit=False)
        for obj in instances:
            self.save_model(request, obj)
        for obj in self.formset.deleted_objects:
            self.delete_model(request, obj)

    def get_has_file_field(self):
        return formset_has_file_field(self.formset.form)

    def save_model(self, request, obj):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()


class TabularInlineFormView(InlineFormView):
    template_name = 'forms/tabular_inline_formset.html'


class StackedInlineFormView(InlineFormView):
    template_name = 'forms/stacked_inline_formset.html'
