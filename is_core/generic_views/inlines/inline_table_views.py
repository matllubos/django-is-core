from django.forms.models import _get_foreign_key

from is_core.generic_views.table_views import TableViewMixin
from is_core.generic_views.inlines import InlineView


class InlineTableView(TableViewMixin, InlineView):

    template_name = 'is_core/forms/inline_table.html'
    fk_name = None

    def _get_api_url(self):
        from is_core.site import get_model_core
        return get_model_core(self.model).get_api_url(self.request)

    def _get_menu_group_pattern_name(self):
        from is_core.site import get_model_core
        return get_model_core(self.model).get_menu_group_pattern_name()

    def _get_list_filter(self):
        list_filter = super(InlineTableView, self)._get_list_filter()
        fk_name = _get_foreign_key(self.parent_instance.__class__, self.model, fk_name=self.fk_name).name
        list_filter['filter'] = filter = list_filter.get('filter', {})
        if 'filter' in list_filter:
            filter[fk_name] = self.parent_instance.pk
        return list_filter
