from django.utils.encoding import force_text
from django.utils import six

from piston.utils import RestFieldset, RestField, get_model_from_descriptor


def generate_subfield(submodel, subfield_name, field_class):
    if subfield_name and submodel:
        return field_class.create_from_string(subfield_name, submodel)
    elif submodel:
        return field_class('_obj_name')


class ModelRestFieldMixin(object):

    @classmethod
    def create_from_string(cls, full_field_name, model):
        subfield_name = None
        if '__' in full_field_name:
            full_field_name, subfield_name = full_field_name.split('__', 1)

        submodel = get_model_from_descriptor(model, full_field_name)
        return cls(full_field_name, generate_subfield(submodel, subfield_name, cls))


class ModelRestField(ModelRestFieldMixin, RestField):

    def __init__(self, name, subfield=None):
        if isinstance(subfield, type(self)):
            subfield = ModelRestFieldset(subfield)
        super(ModelRestField, self).__init__(name, subfield)


class ModelRestFlatField(ModelRestFieldMixin):

    def __init__(self, name, subfield=None):
        assert isinstance(name, six.string_types)
        assert subfield is None or isinstance(subfield, ModelRestFlatField)

        self.name = name
        self.subfield = subfield

    def __str__(self):
        if self.subfield:
            return '%s__%s' % (self.name, self.subfield)
        return '%s' % self.name


class ModelFlatRestFieldsMixin(object):

    @classmethod
    def create_from_flat_list(cls, fields_list, model):
        return cls(*[cls.fields_class.create_from_string(full_field_name, model)
                     for full_field_name in fields_list])


class ModelFlatRestFields(ModelFlatRestFieldsMixin):

    fields_class = ModelRestFlatField

    def __init__(self, *fields):
        self.fields = fields

    def __str__(self):
        return ','.join(map(force_text, self.fields))


class ModelRestFieldset(RestFieldset, ModelFlatRestFieldsMixin):

    fields_class = ModelRestField
