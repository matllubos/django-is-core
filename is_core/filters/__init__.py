from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import RelatedField
from django.db.models.fields import FieldDoesNotExist

from chamber.utils import get_class_method

from is_core.filters.exceptions import FilterException
from is_core.filters.default_filters import *


def get_model_field_or_method_filter(full_field_term, model, value=None, filter_term=None):
    if not filter_term:
        filter_term = full_field_term

    next_filter_term = None
    current_filter_term = filter_term

    if '__' in filter_term:
        current_filter_term, next_filter_term = filter_term.split('__', 1)

    field_or_method = None
    try:
        field_or_method = model._meta.get_field(current_filter_term)

        if (next_filter_term and next_filter_term not in field_or_method.filter.get_suffixes()
            and isinstance(field_or_method, RelatedField)):
            return get_model_field_or_method_filter(filter_term, model._meta.get_field(current_filter_term).rel.to,
                                                    value, next_filter_term)

    except FieldDoesNotExist:
        field_or_method = get_class_method(model, current_filter_term)
        if field_or_method:
            if hasattr(field_or_method, 'filter_by'):
                full_field_term = full_field_term[:-len(current_filter_term)] + field_or_method.filter_by
                return get_model_field_or_method_filter(full_field_term, model, value, field_or_method.filter_by)
        else:
            raise FilterException(_('Not valid filter: %s') % full_field_term)

    if (hasattr(field_or_method, 'filter') and
        (not next_filter_term or next_filter_term in field_or_method.filter.get_suffixes()) and
        field_or_method.filter):
        return field_or_method.filter(filter_term, full_field_term, field_or_method, value)
    else:
        raise FilterException(_('Not valid filter: %s') % full_field_term)
