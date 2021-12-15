from pyston.contrib.elasticsearch.filters import ElasticsearchFilterManager, DateTimeElasticsearchFilter

from is_core.rest.filters import UIFilterMixin
from is_core.forms.widgets import DateTimeRangeFilterWidget


class DateTimeRangeFieldFilter(UIFilterMixin, DateTimeElasticsearchFilter):

    widget = DateTimeRangeFilterWidget


class CoreElasticsearchFilterManagerFilterManager(ElasticsearchFilterManager):

    filter_by_field_name = {
        **ElasticsearchFilterManager.filter_by_field_name,
        'date': DateTimeRangeFieldFilter,
    }
