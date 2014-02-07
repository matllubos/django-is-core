from django.forms.models import inlineformset_factory, ModelForm

from is_core.form.models import BaseInlineFormSet


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

    def __init__(self, request, core, parent_model, instance):
        self.request = request
        self.parent_model = parent_model
        self.core = core
        self.parent = instance
        self.formset = self.get_formset(instance, self.request.POST)

    def get_exclude(self):
        return self.exclude

    def get_fields(self):
        return self.fields

    def get_extra(self):
        return self.extra

    def get_readonly_fields(self):
        return self.readonly_fields

    def get_fieldset(self, formset):
        fields = self.get_fields() or formset.form.base_fields.keys()
        fields = list(fields) + list(self.readonly_fields)
        if self.can_delete:
            fields.append('DELETE')
        return fields

    def get_formset_factory(self):
        extra = self.get_extra()
        exclude = self.get_exclude() + self.get_readonly_fields()
        return inlineformset_factory(self.parent_model, self.model, form=self.form_class,
                                     fk_name=self.fk_name, extra=extra, formset=BaseInlineFormSet,
                                     can_delete=self.get_can_delete(), exclude=exclude,
                                     fields=self.fields)

    def get_queryset(self):
        return self.model.objects.all()

    def get_can_delete(self):
        return self.can_delete

    def get_can_add(self):
        return self.can_add

    def get_formset(self, instance, data):
        if data:
            # data = remove
            formset = self.get_formset_factory()(data=data, instance=instance, queryset=self.get_queryset())
        else:
            formset = self.get_formset_factory()(instance=instance, queryset=self.get_queryset())

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

    def save_model(self, request, obj):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()


class TabularInlineFormView(InlineFormView):
    template_name = 'forms/tabular_inline_formset.html'


class StackedInlineFormView(InlineFormView):
    template_name = 'forms/stacked_inline_formset.html'
