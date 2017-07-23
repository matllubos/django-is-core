Filters
=======

Filters are documented inside django-pyston. Is core uses Pyston filters to generate list view. Every column can
contain form input which accepts inputu data. There is several options how is django widget which is used for rendering
HTML of filter input:

UIFilterMixin
^^^^^^^^^^^^^

Django-is-core provedes special mixin for filters that adds posibility to change rendered widget inside filter class,
example exclude ``ForeignKeyFilter`` with posibility to restrict field queryset choices::

    class RestrictedFkFilter(UIFilterMixin, ForeignKeyFilter):

        def get_restricted_queryset(self, qs, request):
            # There can be foreign key queryset restricted
            return qs

        def get_widget(self, request):
            formfield = self.field.formfield()
            formfield.queryset = self.get_restricted_queryset(formfield.queryset, request)
            return formfield.widget


Field filter
^^^^^^^^^^^^

There is two possibilities. If filter has set choices attribute, filter is always select box with filter choices. If not
filter is obtained from model field by using method ``formfield``.

Method/Resource filter
^^^^^^^^^^^^^^^^^^^^^^

There is applied same rule as for field filter, but if choices is not defined is returned simple text input.
