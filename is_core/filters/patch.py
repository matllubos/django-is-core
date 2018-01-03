from pyston.patch import DateField, DateTimeField, ManyToManyField, ForeignKey, ForeignObjectRel

from .default_filters import (
    DateRangeFilter, DateTimeRangeFilter, UIManyToManyFieldFilter, UIForeignKeyFilter, UIForeignObjectRelFilter
)


DateField.default_filter = DateRangeFilter
DateTimeField.default_filter = DateTimeRangeFilter
ManyToManyField.default_filter = UIManyToManyFieldFilter
ForeignKey.default_filter = UIForeignKeyFilter
ForeignObjectRel.default_filter = UIForeignObjectRelFilter
