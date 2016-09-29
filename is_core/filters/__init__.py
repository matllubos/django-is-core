from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as ugettext
from django.db.models.fields.related import RelatedField
from django.db.models.fields import FieldDoesNotExist

from chamber.utils import get_class_method

from is_core.filters.exceptions import FilterException


def get_field_method_or_none(model, name):
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist:
        try:
            return get_class_method(model, name)
        except (AttributeError, FieldDoesNotExist):
            return None


def get_model_field_or_method_filter(full_field_term, model, value=None, filter_term=None, ui=False):
    filter_term = full_field_term if not filter_term else filter_term
    current_filter_term, next_filter_term = filter_term.split('__', 1) if '__' in filter_term else (filter_term, None)

    field_or_method = get_field_method_or_none(model, current_filter_term)

    if (field_or_method and next_filter_term and next_filter_term not in field_or_method.filter.get_suffixes() and
            isinstance(field_or_method, RelatedField)):
        return get_model_field_or_method_filter(filter_term, model._meta.get_field(current_filter_term).rel.to,
                                                value, next_filter_term, ui=ui)
    elif ui and hasattr(field_or_method, 'filter_by'):
        return get_model_field_or_method_filter(
            full_field_term[:-len(current_filter_term)] + field_or_method.filter_by, model, value,
            field_or_method.filter_by, ui=ui)
    elif ui and (isinstance(field_or_method, RelatedField) and not next_filter_term and
              field_or_method.rel.model._ui_meta.default_ui_filter_by):
        return get_model_field_or_method_filter(
            '{}__{}'.format(full_field_term, field_or_method.rel.model._ui_meta.default_ui_filter_by),
            field_or_method.rel.model, value, field_or_method.rel.model._ui_meta.default_ui_filter_by, ui=ui)
    elif (hasattr(field_or_method, 'filter') and
            (not next_filter_term or next_filter_term == 'not' or
                next_filter_term in field_or_method.filter.get_suffixes()) and
            field_or_method.filter):
        return field_or_method.filter(filter_term, full_field_term, field_or_method, value)
    else:
        raise FilterException(ugettext('Not valid filter: {}').format(full_field_term))
