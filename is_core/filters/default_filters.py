from django import forms

from pyston.filters.default_filters import (
    DateFilter, ManyToManyFieldFilter, OPERATORS, ForeignKeyFilter, ForeignObjectRelFilter
)

from is_core.forms.widgets import DateRangeFilterWidget, DateTimeRangeFilterWidget, RestrictedSelectWidget

from . import UIFilterMixin, FilterChoiceIterator


class DateRangeFilter(UIFilterMixin, DateFilter):
    """
    UI filter for date field that provides possibility to filter date from/to
    """

    widget = DateRangeFilterWidget


class DateTimeRangeFilter(UIFilterMixin, DateFilter):
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


class UIForeignKeyFilter(RelatedUIFilter, ForeignKeyFilter):

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
