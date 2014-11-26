from piston.utils import RestFieldset, RestField


def get_model_from_descriptor(model, field_name):
    model_descriptor = getattr(model, field_name, None)
    if model_descriptor and hasattr(model_descriptor, 'related'):
        return model_descriptor.related.model
    elif model_descriptor and hasattr(model_descriptor, 'field'):
        return model_descriptor.field.rel.to


def generate_subfieldset(submodel, subfield_name):
    if subfield_name and submodel:
        return ModelRestFieldset(ModelRestField.create_from_string(subfield_name, submodel))
    elif submodel:
        return ModelRestFieldset('_obj_name')


class ModelRestField(RestField):

    @classmethod
    def create_from_string(cls, full_field_name, model):
        subfield_name = None
        if '__' in full_field_name:
            full_field_name, subfield_name = full_field_name.split('__', 1)

        submodel = get_model_from_descriptor(model, full_field_name)
        return ModelRestField(full_field_name, generate_subfieldset(submodel, subfield_name))


class ModelRestFieldset(RestFieldset):

    @classmethod
    def create_from_flat_list(cls, fields_list, model):
        return ModelRestFieldset(*[ModelRestField.create_from_string(full_field_name, model)
                                   for full_field_name in  fields_list])
