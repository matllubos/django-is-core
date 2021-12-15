from django import forms
from django.db.models.fields import DateField, DateTimeField
from django.db.models.fields.related import ForeignKey, ManyToManyField, ForeignObjectRel

from pyston.filters.filters import OPERATORS, NONE_LABEL
from pyston.filters.managers import DjangoFilterManager
from pyston.filters.django_filters import (
    DateFieldFilter, ManyToManyFieldFilter, ForeignKeyFieldFilter, ForeignObjectRelFilter
)

from is_core.forms.widgets import DateRangeFilterWidget, DateTimeRangeFilterWidget, RestrictedSelectWidget


class FilterChoiceIterator:
    """
    Filter iterator surrounds default model iterator, removes blank values and adds possibilities
    to remove filtered value (blank) and filter according to "None" value.
    """

    def __init__(self, choices, field=None):
        self.choices = choices
        self.field = field

    def __iter__(self):
        yield ('', '')

        if self.field and (self.field.null or self.field.blank):
            yield ('__none__', NONE_LABEL)

        for k, v in self.choices:
            if k is not None and k != '':
                yield (k, v)

    def __len__(self):
        return len(self.choices)

    def __getattr__(self, name):
        return getattr(self.choices, name)


class UIFilterMixin:
    """
    Special mixin for improve Pyston filters. There can be defined UI appearance (widget) and used operator.
    """

    widget = None

    def get_widget(self, request):
        """
        Returns concrete widget that will be used for rendering table filter.
        """
        widget = self.widget
        if isinstance(widget, type):
            widget = widget()
        return widget

    def get_operator(self, widget):
        """
        Returns operator used for filtering. By default it is first operator defined in Pyston filter.
        """
        return self.get_allowed_operators()[0]


class DateRangeFieldFilter(UIFilterMixin, DateFieldFilter):
    """
    UI filter for date field that provides possibility to filter date from/to
    """

    widget = DateRangeFilterWidget


class DateTimeRangeFieldFilter(UIFilterMixin, DateFieldFilter):
    """
    UI filter for datetime field that provides possibility to filter date from/to
    """

    widget = DateTimeRangeFilterWidget


class RelatedUIFilter(UIFilterMixin):
    """
    Helper for all filters of related field.
    """

    def _update_widget_choices(self, widget):
        """
        Updates widget choices with special choice iterator that removes blank values and adds none value to clear
        filter data.
        :param widget: widget with choices
        :return: updated widget with filter choices
        """

        widget.choices = FilterChoiceIterator(widget.choices, self.field)
        return widget

    def get_operator(self, widget):
        """
        Because related form field can be restricted (if choices is too much it is used textarea without select box)
        for situation without choices (textarea) is used contains operator.
        :param widget: restricted widget
        :return: operator that will be used for filtering
        """
        return OPERATORS.CONTAINS if widget.is_restricted else OPERATORS.EQ


class UIForeignKeyFieldFilter(RelatedUIFilter, ForeignKeyFieldFilter):

    def get_widget(self, request):
        """
        Field widget is replaced with "RestrictedSelectWidget" because we not want to use modified widgets for
        filtering.
        """
        return self._update_widget_choices(self.field.formfield(widget=RestrictedSelectWidget).widget)


class UIManyToManyFieldFilter(RelatedUIFilter, ManyToManyFieldFilter):

    def get_widget(self, request):
        """
        Field widget is replaced with "RestrictedSelectWidget" because "MultipleChoiceField" is not optional for
        filtering purposes.
        """
        return self._update_widget_choices(self.field.formfield(widget=RestrictedSelectWidget).widget)


class UIForeignObjectRelFilter(RelatedUIFilter, ForeignObjectRelFilter):

    def get_widget(self, request):
        """
        Table view is not able to get form field from reverse relation.
        Therefore this widget returns similar form field as direct relation (ModelChoiceField).
        Because there is used "RestrictedSelectWidget" it is returned textarea or selectox with choices according to
        count objects in the queryset.
        """
        return self._update_widget_choices(
            forms.ModelChoiceField(
                widget=RestrictedSelectWidget, queryset=self.field.related_model._default_manager.all()
            ).widget
        )


class CoreDjangoFilterManager(DjangoFilterManager):

    model_field_filters = {
        DateField: DateRangeFieldFilter,
        DateTimeField: DateTimeRangeFieldFilter,
        ManyToManyField: UIManyToManyFieldFilter,
        ForeignKey: UIForeignKeyFieldFilter,
        ForeignObjectRel: UIForeignObjectRelFilter,
    }
