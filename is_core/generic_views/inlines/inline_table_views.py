from django.forms.models import _get_foreign_key

from is_core.generic_views.table_views import TableViewMixin
from is_core.generic_views.inlines import InlineView
from is_core.site import get_model_core


class InlineTableView(TableViewMixin, InlineView):
    template_name = 'forms/inline_table.html'
    fk_name = None

    def _get_api_url(self):
        return get_model_core(self.model).get_api_url(self.request)

    def _get_menu_group_pattern_name(self):
        return get_model_core(self.model).get_menu_group_pattern_name()

    def _get_list_filter(self):
        fk_name = _get_foreign_key(self.parent_instance.__class__, self.model, fk_name=self.fk_name).name
        return {'filter': {fk_name: self.parent_instance.pk}}
