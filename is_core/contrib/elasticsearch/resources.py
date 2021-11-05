from elasticsearch import NotFoundError

from is_core.rest.resource import ModelCoreResourceMixin

from pyston.contrib.elasticsearch.resource import BaseElasticsearchResource


class ElasticsearchCoreResource(ModelCoreResourceMixin, BaseElasticsearchResource):

    def _get_obj_or_none(self, pk=None):
        if not pk:
            return None
        try:
            return self.core.model.get(id=pk)
        except NotFoundError:
            return None
