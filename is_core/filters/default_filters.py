from django import forms

from is_core.forms.widgets import DateRangeFilterWidget, DateTimeRangeFilterWidget
from pyston.filters.default_filters import DateFilter, ForeignObjectRelFilter, ManyToManyFieldFilter

from . import UIFilterMixin


class ISCoreDateRangeFilter(UIFilterMixin, DateFilter):

    widget = DateRangeFilterWidget


class ISCoreDateTimeRangeFilter(UIFilterMixin, DateFilter):

    widget = DateTimeRangeFilterWidget


class ISCoreForeignObjectRelFilter(UIFilterMixin, ForeignObjectRelFilter):

    widget = forms.TextInput()


class ISCoreManyToManyFieldFilter(UIFilterMixin, ManyToManyFieldFilter):

    widget = forms.TextInput()