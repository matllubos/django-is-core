from pyston.serializer import ModelResourceSerializer


class ISCoreModelResourceSerializer(ModelResourceSerializer):

    def _get_resource_method_fields(self, resource, fields):
        out = {}
        for field in fields.flat() - self.RESERVED_FIELDS:
            t = getattr(resource, str(field), None) or getattr(resource.core, str(field), None)
            if t and callable(t):
                out[field] = t
        return out