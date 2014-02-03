from django.forms.models import inlineformset_factory, ModelForm

from is_core.form.models import BaseInlineFormSet
from is_core.form import form_to_readonly


class InlineFormView(object):
    form_class = ModelForm
    model = None
    fk_name = None
    template_name = None
    extra = 0
    exclude = None
    can_add = True
    can_delete = True

    def __init__(self, request, core, parent_model, instance, readonly):
        self.request = request
        self.parent_model = parent_model
        self.readonly = readonly
        self.core = core
        self.parent = instance
        self.formset = self.get_formset(instance, self.request.POST)

    def get_exclude(self):
        return self.exclude

    def get_extra(self):
        return self.extra

    def get_formset_factory(self):
        extra = not self.is_readonly() and self.get_extra() or 0
        return inlineformset_factory(self.parent_model, self.model, form=self.form_class,
                                     fk_name=self.fk_name, extra=extra, formset=BaseInlineFormSet,
                                     can_delete=self.get_can_delete(), exclude=self.get_exclude())

    def get_queryset(self):
        return self.model.objects.all()

    def get_can_delete(self):
        return self.can_delete and not self.is_readonly()

    def get_can_add(self):
        return self.can_add and not self.is_readonly()

    def get_formset(self, instance, data):
        if data and not self.is_readonly():
            formset = self.get_formset_factory()(data=data, instance=instance, queryset=self.get_queryset())
        else:
            formset = self.get_formset_factory()(instance=instance, queryset=self.get_queryset())

        formset.can_add = self.get_can_add()
        formset.can_delete = self.get_can_delete()
        formset.readonly = False

        if self.is_readonly():
            formset.readonly = True
            for form in formset:
                form_to_readonly(form)
        return formset

    def is_readonly(self):
        return self.readonly

    def get_name(self):
        return self.model.__name__

    def form_valid(self, request):
        if not self.is_readonly():
            instances = self.formset.save(commit=False)
            for obj in instances:
                self.save_model(request, obj)
            for obj in self.formset.deleted_objects:
                self.delete_model(request, obj)

    def save_model(self, request, obj):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()


class TabularInlineFormView(InlineFormView):
    template_name = 'forms/tabular_inline_formset.html'


class StackedInlineFormView(InlineFormView):
    template_name = 'forms/stacked_inline_formset.html'
