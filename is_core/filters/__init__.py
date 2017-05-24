from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as ugettext
from django.db.models.fields import FieldDoesNotExist

from chamber.utils import get_class_method

from is_core.filters.exceptions import FilterException, FilterValueException


def get_field_or_none(model, name):
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist as ex:
        return None


def get_method_or_none(model, name):
    try:
        return get_class_method(model, name)
    except (AttributeError, FieldDoesNotExist):
        return None


def get_model_field_filter(field, full_field_term, filter_term, ui):
    current_filter_term, next_filter_term = filter_term.split('__', 1) if '__' in filter_term else (filter_term, None)
    if (next_filter_term and next_filter_term not in field.filter.get_suffixes_with_not() and
          not field.auto_created and (field.many_to_one or field.one_to_one or field.many_to_many)):
        return get_model_field_or_method_filter(full_field_term, field.rel.to, next_filter_term, ui=ui)
    elif (next_filter_term and next_filter_term not in field.filter.get_suffixes_with_not() and
           field.auto_created and (field.one_to_many or field.one_to_one or field.many_to_many)):
        return get_model_field_or_method_filter(full_field_term, field.related_model, next_filter_term, ui=ui)
    elif (ui and not field.auto_created and (field.many_to_one or field.one_to_one or field.many_to_many) and
           not next_filter_term and field.rel.model._ui_meta.default_ui_filter_by):
        return get_model_field_or_method_filter(
            '{}__{}'.format(full_field_term, field.rel.model._ui_meta.default_ui_filter_by),
            field.rel.model, field.rel.model._ui_meta.default_ui_filter_by, ui=ui)
    elif (ui and field.auto_created and (field.one_to_many or field.one_to_one or field.many_to_many) and
           not next_filter_term and field.related_model._ui_meta.default_ui_filter_by):
        return get_model_field_or_method_filter(
            '{}__{}'.format(full_field_term, field.related_model._ui_meta.default_ui_filter_by),
            field.related_model, field.related_model._ui_meta.default_ui_filter_by, ui=ui)
    elif (hasattr(field, 'filter') and
            (not next_filter_term or next_filter_term in field.filter.get_suffixes_with_not())):
        return field.filter(filter_term, full_field_term, field)
    else:
        raise FilterException(ugettext('Not valid filter: {}').format(full_field_term))


def get_model_method_filter(method, full_field_term, model, filter_term, ui=False):
    current_filter_term, next_filter_term = filter_term.split('__', 1) if '__' in filter_term else (filter_term, None)
    if ui and hasattr(method, 'filter_by'):
        return get_model_field_or_method_filter(
            full_field_term[:-len(current_filter_term)] + method.filter_by, model, method.filter_by, ui=ui)
    elif (hasattr(method, 'filter') and
            (not next_filter_term or next_filter_term in method.filter.get_suffixes_with_not())):
        return method.filter(filter_term, full_field_term, method)
    else:
        raise FilterException(ugettext('Not valid filter: {}').format(full_field_term))


def get_model_field_or_method_filter(full_field_term, model, filter_term=None, ui=False):
    filter_term = full_field_term if not filter_term else filter_term
    current_filter_term, next_filter_term = filter_term.split('__', 1) if '__' in filter_term else (filter_term, None)

    field = get_field_or_none(model, current_filter_term)
    method = get_method_or_none(model, filter_term)
    if field:
        return get_model_field_filter(field, full_field_term, filter_term, ui)
    elif method:
        return get_model_method_filter(method, full_field_term, model, filter_term, ui)
    else:
        raise FilterException(ugettext('Not valid filter: {}').format(full_field_term))
