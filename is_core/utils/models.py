from django.core.exceptions import FieldDoesNotExist


def get_model_field_names(model):
    return [model_field.name for model_field in model._meta.fields] + ['pk']


def get_model_field_by_name(model, field_name):
    try:
        return model._meta.get_field_by_name(field_name)[0]
    except FieldDoesNotExist:
        return None


def get_model_field_value(field_name, instance):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        return get_model_field_value(next_field_name, getattr(instance, current_field_name))
    else:
        try:
            callable_value = getattr(instance, 'get_%s_display' % field_name, None)
            if not callable_value:
                callable_value = getattr(instance, field_name)
            if hasattr(callable_value, '__call__'):
                value = callable_value()
            else:
                value = callable_value
            return value
        except ValueError:
            return ''
