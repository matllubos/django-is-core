from django.shortcuts import _get_queryset


def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def get_model_field_names(model):
    return [model_field.name for model_field in model._meta.fields] + ['pk']


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
