from is_core.forms.widgets import DateRangeFilterWidget, DateTimeRangeFilterWidget
from pyston.filters.default_filters import DateFilter

from . import UIFilterMixin


class DateRangeFilter(UIFilterMixin, DateFilter):

    widget = DateRangeFilterWidget


class DateTimeRangeFilter(UIFilterMixin, DateFilter):

    widget = DateTimeRangeFilterWidget
