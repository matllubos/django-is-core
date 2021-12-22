from elasticsearch import NotFoundError

from is_core.generic_views.detail_views import ModelReadonlyDetailView
from is_core.generic_views.inlines.inline_table_views import BaseModelInlineTableView
from is_core.generic_views.table_views import BaseModelTableView
from is_core.utils.field_api import BaseModelFieldDescriptor, pretty_name

from elasticsearch_dsl import Document


class ElasticsearcDocumenthFieldDescriptor(BaseModelFieldDescriptor):

    is_model_field = True
    base_model = Document

    @classmethod
    def init_descriptor_or_none(cls, model, field_name, view):
        model_field = model._doc_type.mapping.properties.to_dict()['properties'].get(field_name)
        return cls(model, field_name, model_field) if model_field else None

    def get_label(self):
        return getattr(self.model_field_or_method, 'short_description', pretty_name(self.field_name))

    def get_value(self, instance, request=None):
        return getattr(instance, self.field_name)


class ElasticsearchTableViewMixin:

    list_verbose_name = '%(verbose_name_plural)s'

    @property
    def model_name(self):
        return str(self.model.__class__.__name__.lower())


class ElasticsearchInlineTableView(ElasticsearchTableViewMixin, BaseModelInlineTableView):
    pass


class ElasticsearchTableView(ElasticsearchTableViewMixin, BaseModelTableView):

    add_button_verbose_name = 'add %(verbose_name)s'


class ElasticsearchDetailView(ModelReadonlyDetailView):

    detail_verbose_name = '%(verbose_name)s'

    def _get_obj_or_none(self):
        if not self.kwargs.get('pk'):
            return None
        try:
            return self.model.get(id=self.kwargs.get('pk'))
        except NotFoundError:
            return None
