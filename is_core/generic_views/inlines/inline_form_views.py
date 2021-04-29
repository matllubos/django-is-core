from django.forms.formsets import DELETION_FIELD_NAME
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from chamber.utils.forms import formset_has_file_field

from is_core.forms.models import BaseInlineFormSet, smartinlineformset_factory, SmartModelForm
from is_core.generic_views.inlines import RelatedInlineView
from is_core.forms.fields import SmartReadonlyField, EmptyReadonlyField
from is_core.utils import get_readonly_field_data, GetMethodFieldMixin


class InlineFormView(GetMethodFieldMixin, RelatedInlineView):

    form_class = SmartModelForm
    base_inline_formset_class = BaseInlineFormSet

    fields = None
    exclude = ()
    inline_views = None
    field_labels = None

    template_name = None

    fk_name = None
    extra = 0
    can_add = True
    can_delete = True
    is_readonly = False
    max_num = None
    min_num = 0
    readonly_fields = ()
    initial = []
    no_items_text = _('There are no items')
    class_names = ['inline-js']
    add_inline_button_verbose_name = None
    save_before_parent = False

    def __init__(self, request, parent_view, parent_instance):
        super().__init__(request, parent_view, parent_instance)
        self.core = parent_view.core
        self.parent_instance = parent_instance
        self.parent_model = self.parent_instance.__class__
        self.readonly = self._is_readonly()

    @cached_property
    def formset(self):
        return self.get_formset()

    def _get_field_labels(self):
        return self.field_labels

    def _is_readonly(self):
        return self.is_readonly or self.parent_view.is_readonly()

    def can_form_delete(self, form):
        return (
            not self.is_form_readonly(form)
            and self.permission.has_permission('delete', self.request, self, obj=form.instance)
        )

    def is_form_readonly(self, form):
        return self.readonly and self.permission.has_permission('update', self.request, self, obj=form.instance)

    def get_context_data(self, **kwargs):
        formset = self.formset
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'formset': formset,
            'fields': self.get_fromset_fields(formset),
            'name': self.get_name(),
            'button_value': self.get_button_value(),
            'class_names': self.get_class_names(formset, **kwargs),
            'no_items_text': self.no_items_text
        })
        return context_data

    def get_class_names(self, formset, **kwargs):
        class_names = self.class_names + [self.get_name().lower()]
        if formset.can_add:
            class_names.append('can-add')
        if formset.can_delete:
            class_names.append('can-delete')

        if kwargs.get('title'):
            class_names.append('with-title')
        else:
            class_names.append('without-title')

        return class_names

    def get_exclude(self):
        return self.exclude

    def generate_fields(self):
        fields = self.get_fields()
        if fields is None:
            fields = (
                list(self.get_form_class().base_fields.keys())
                + list(self.get_formset_factory().form.base_fields.keys())
            )
        return [field for field in fields if field not in self._get_disallowed_fields_from_permissions()]

    def get_fields(self):
        return self.fields

    def get_extra(self):
        return self.extra + len(self.get_initial())

    def get_initial(self):
        return self.initial[:]

    def get_can_delete(self):
        return (
            (self.get_can_add() or (self.can_delete and self.permission.has_permission('delete', self.request, self)))
            and not self.readonly
        )

    def get_can_add(self):
        return self.can_add and not self.readonly and self.permission.has_permission('create', self.request, self)

    def get_readonly_fields(self):
        return self.readonly_fields

    def generate_readonly_fields(self):
        return list(self.get_readonly_fields()) + list(self._get_readonly_fields_from_permissions())

    def get_prefix(self):
        return '-'.join((self.parent_view.get_prefix(), 'inline', self.__class__.__name__)).lower()

    def get_fromset_fields(self, formset):
        fields = list(self.generate_fields() or formset.form.base_fields.keys())
        if formset.can_delete:
            fields.append(DELETION_FIELD_NAME)
        return fields

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def formfield_for_readonlyfield(self, name, **kwargs):
        def _get_readonly_field_data(instance):
            return get_readonly_field_data(instance, name, self.request, view=self)
        return SmartReadonlyField(_get_readonly_field_data)

    def get_form_class(self):
        return self.form_class

    def get_max_num(self):
        return self.max_num

    def get_min_num(self):
        return self.min_num

    def get_formset_factory(self, fields=None, readonly_fields=()):
        return smartinlineformset_factory(
            self.parent_model, self.model, self.request, form=self.get_form_class(), fk_name=self.fk_name,
            extra=self.get_extra(), formset=self.base_inline_formset_class, exclude=self.get_exclude(),
            fields=fields, min_num=self.get_min_num(), max_num=self.get_max_num(), readonly_fields=readonly_fields,
            readonly=self._is_readonly(), formreadonlyfield_callback=self.formfield_for_readonlyfield,
            formfield_callback=self.formfield_for_dbfield, labels=self._get_field_labels(),
            can_delete=self.get_can_delete()
        )

    def get_queryset(self):
        return self.model.objects.all()

    def get_formset(self):
        fields = self.generate_fields()
        readonly_fields = self.generate_readonly_fields()

        if self.request.POST:
            formset = self.get_formset_factory(fields, readonly_fields)(data=self.request.POST,
                                                                        files=self.request.FILES,
                                                                        instance=self.parent_instance,
                                                                        queryset=self.get_queryset(),
                                                                        prefix=self.get_prefix())
        else:
            formset = self.get_formset_factory(fields, readonly_fields)(instance=self.parent_instance,
                                                                        queryset=self.get_queryset(),
                                                                        initial=self.get_initial(),
                                                                        prefix=self.get_prefix())

        formset.can_add = self.get_can_add()
        for form in formset.all_forms():
            form.class_names = self.form_class_names(form)
            form._is_readonly = self.is_form_readonly(form)
            if not self.readonly and form._is_readonly:
                if formset.can_delete:
                    form.readonly_fields = set(form.fields.keys()) - {'id', DELETION_FIELD_NAME}
                else:
                    form.readonly_fields = set(form.fields.keys()) - {'id'}

            if formset.can_delete and form.instance.pk and not self.can_form_delete(form):
                form.fields[DELETION_FIELD_NAME] = EmptyReadonlyField(
                    required=form.fields[DELETION_FIELD_NAME].required,
                    label=form.fields[DELETION_FIELD_NAME].label
                )
                form.readonly_fields |= {DELETION_FIELD_NAME}

            self.init_form(form)

        for i in range(self.get_min_num()):
            formset.forms[i].empty_permitted = False
        return formset

    def form_class_names(self, form):
        if not form.instance.pk:
            return ['empty']
        return []

    def init_form(self, form):
        self.form_fields(form)

    def form_fields(self, form):
        for field_name, field in form.fields.items():
            self.form_field(form, field_name, field)

    def form_field(self, form, field_name, form_field):
        placeholder = self.model._ui_meta.placeholders.get('field_name', None)
        if placeholder:
            form_field.widget.placeholder = self.model._ui_meta.placeholders.get('field_name', None)
        return form_field

    def get_name(self):
        return self.model.__name__

    def get_button_value(self):
        return self.add_inline_button_verbose_name or self.model._ui_meta.add_inline_button_verbose_name % {
            'verbose_name': self.model._meta.verbose_name,
            'verbose_name_plural': self.model._meta.verbose_name_plural
        }

    def form_valid(self, request):
        formset = self.formset
        instances = formset.save(commit=False)
        for obj in instances:
            change = obj.pk is not None
            self.save_obj(obj, change)
        for obj in formset.deleted_objects:
            self.delete_obj(obj)
        formset.save_m2m()

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

    def is_valid(self):
        return self.formset.is_valid()

    def has_changed(self):
        return self.formset.has_changed()


class TabularInlineFormView(InlineFormView):

    template_name = 'is_core/forms/tabular_inline_formset.html'


class StackedInlineFormView(InlineFormView):

    template_name = 'is_core/forms/stacked_inline_formset.html'


class ResponsiveInlineFormView(InlineFormView):

    template_name = 'is_core/forms/responsive_inline_formset.html'
