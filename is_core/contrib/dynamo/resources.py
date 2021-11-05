from is_core.rest.resource import ModelCoreResourceMixin

from pyston.contrib.dynamo.resource import BaseDynamoResource


class DynamoCoreResource(ModelCoreResourceMixin, BaseDynamoResource):

    def get_range_key(self):
        return self.core.rest_range_key if self.range_key is None else self.range_key

    def _get_hash_key(self):
        return self.core._get_hash_key(self.request)

    def _get_obj_or_none(self, pk=None):
        return self.core.get_obj(self.request, pk)
