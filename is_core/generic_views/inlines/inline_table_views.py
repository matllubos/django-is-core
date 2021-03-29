from django.forms.models import _get_foreign_key

from is_core.config import settings
from is_core.generic_views.table_views import TableViewMixin
from is_core.generic_views.inlines import RelatedInlineView


class InlineTableView(TableViewMixin, RelatedInlineView):

    template_name = 'is_core/forms/inline_table.html'
    fk_name = None

    def _get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None or not self.related_core
            else self.related_core.get_ui_field_labels(self.request)
        )

    def _get_fields(self):
        return (
            self.related_core.get_ui_list_fields(self.request) if self.related_core and self.fields is None
            else self.fields
        )

    def _get_export_fields(self):
        return (
            self.related_core.get_ui_export_fields(self.request) if self.related_core and self.export_fields is None
            else self.export_fields
        )

    def _get_list_per_page(self):
        list_per_page = self.related_core.get_list_per_page(self.request) if self.related_core else None
        return list_per_page if list_per_page is not None else super()._get_list_per_page()

    def _get_api_url(self):
        return self.related_core.get_api_url(self.request)

    def _get_menu_group_pattern_name(self):
        return self.related_core.get_menu_group_pattern_name()

    def _get_list_filter(self):
        list_filter = super()._get_list_filter()
        fk_name = _get_foreign_key(self.parent_instance.__class__, self.model, fk_name=self.fk_name).name
        list_filter['filter'] = filter = list_filter.get('filter', {})
        if 'filter' in list_filter:
            filter[fk_name] = self.parent_instance.pk
        return list_filter
