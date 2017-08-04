from is_core.forms.widgets import DateRangeWidget, DateTimeRangeWidget
from pyston.filters.default_filters import DateFilter

from . import UIFilterMixin


class DateRangeFilter(UIFilterMixin, DateFilter):

    widget = DateRangeWidget


class DateTimeRangeFilter(UIFilterMixin, DateFilter):

    widget = DateTimeRangeWidget
