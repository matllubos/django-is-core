from django.db.models import Model
from django.utils.functional import lazy

from django.apps import apps
from django.db.models.utils import make_model_tuple


def short_description(description):
    """
    Sets 'short_description' attribute (this attribute is in exports to generate header name).
    """
    def decorator(func):
        if isinstance(func, property):
            func = func.fget
        func.short_description = description
        return func
    return decorator


def relation(to):
    """
    Add relation to the method. Now method can be used in the core field path as a relation.
    :param to: model class or string path to the model class
    """
    def decorator(func):
        if isinstance(func, property):
            func = func.fget

        def set_related_model(model):
            func.related_model = model

        if isinstance(to, str):
            apps.lazy_model_operation(set_related_model, make_model_tuple(to))
        else:
            func.related_model = to
        return func
    return decorator
