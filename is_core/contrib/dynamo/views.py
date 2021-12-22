from is_core.generic_views.inlines.inline_table_views import BaseModelInlineTableView
from is_core.generic_views.table_views import BaseModelTableView
from is_core.generic_views.detail_views import ModelReadonlyDetailView


class DynamoTableViewMixin:

    list_verbose_name = '%(verbose_name_plural)s'

    @property
    def model_name(self):
        return str(self.model.__class__.__name__.lower())


class DynamoInlineTableView(DynamoTableViewMixin, BaseModelInlineTableView):
    pass


class DynamoTableView(DynamoTableViewMixin, BaseModelTableView):

    add_button_verbose_name = 'add %(verbose_name)s'


class DynamoDetailView(ModelReadonlyDetailView):

    detail_verbose_name = '%(verbose_name)s'

    def _get_obj_or_none(self):
        return self.core.get_obj(self.request, self.kwargs['pk'])
