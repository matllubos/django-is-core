from is_core.forms.generic import BaseGenericInlineFormSet, smart_generic_inlineformset_factory


from .inline_form_views import InlineFormView


class GenericInlineFormView(InlineFormView):

    ct_fk_field = 'object_id'
    ct_field = 'content_type'

    base_inline_formset_class = BaseGenericInlineFormSet

    def get_formset_factory(self, fields=None, readonly_fields=()):
        return smart_generic_inlineformset_factory(
            self.model, self.request, form=self.get_form_class(), ct_field=self.ct_field, fk_field=self.ct_fk_field,
            extra=self.get_extra(), formset=self.base_inline_formset_class, exclude=self.get_exclude(), fields=fields,
            min_num=self.get_min_num(), max_num=self.get_max_num(), readonly_fields=readonly_fields,
            readonly=self.readonly, formreadonlyfield_callback=self.formfield_for_readonlyfield,
            formfield_callback=self.formfield_for_dbfield, labels=self._get_field_labels(),
            can_delete=self.get_can_delete()
        )


class TabularGenericInlineFormView(GenericInlineFormView):

    template_name = 'is_core/forms/tabular_inline_formset.html'


class StackedGenericInlineFormView(GenericInlineFormView):

    template_name = 'is_core/forms/stacked_inline_formset.html'


class ResponsiveGenericInlineFormView(GenericInlineFormView):

    template_name = 'is_core/forms/responsive_inline_formset.html'
