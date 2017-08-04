from pyston.patch import DateField, DateTimeField

from .default_filters import DateRangeFilter, DateTimeRangeFilter


DateField.default_filter = DateRangeFilter
DateTimeField.default_filter = DateTimeRangeFilter