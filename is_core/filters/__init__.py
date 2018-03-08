from pyston.filters.default_filters import NONE_LABEL


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