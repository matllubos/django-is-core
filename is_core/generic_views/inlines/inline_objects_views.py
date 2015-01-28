from is_core.generic_views.inlines import InlineView


class InlineObjectsView(InlineView):
    """
    This inline class behaves and displays like 'InlineFormView', which is read-only. No need of any form or queryset.
    Implement method 'get_objects' and define a list of fields in the attribute 'fields'.
    """

    template_name = None

    # Tuple of tuples. The tuple consists of key and value (which will be displayed in template)
    # For eg: (('company_name', _('Company name')), ('zip', _('ZIP code')), ('...', '...'))
    fields = ()

    def get_fields(self):
        return list(self.fields)

    def get_objects(self):
        """
        This method must return a list of models, dictionaries or any objects.

        Dictionaries must have keys defined in the attribute 'fields'. For eg: {'company_name': 'ABC', 'zip': '44455'}

        Objects / models must have attributes defined in the attribute 'fields'. Or it may have a humanizing methods
        'get_attributename_humanized', for eg: method 'get_zip_hunanized'.
        """
        raise NotImplementedError

    def get_data_list(self, fields, objects):
        return [[(field_name, self.get_data_object(field_name, obj)) for field_name, _ in self.get_fields()]
                for obj in objects]

    def get_data_object(self, field_name, obj):
        humanize_method_name = 'get_%s_humanized' % field_name
        if hasattr(getattr(obj, humanize_method_name, None), '__call__'):
            return getattr(obj, humanize_method_name)()
        elif hasattr(obj, field_name):
            return getattr(obj, field_name)
        elif isinstance(obj, dict) and field_name in obj:
            return obj.get(field_name)

    def get_header_list(self, fields):
        return self.get_fields()

    def get_class_names(self):
        return [self.__class__.__name__.lower(),]

    def get_context_data(self, **kwargs):
        context_data = super(InlineObjectsView, self).get_context_data(**kwargs)
        context_data.update({
            'data_list': self.get_data_list(self.get_fields(), self.get_objects()),
            'header_list': self.get_header_list(self.get_fields()),
            'class_names': self.get_class_names(),
            })
        return context_data


class TabularInlineObjectsView(InlineObjectsView):
    template_name = 'forms/tabular_inline_objects.html'


class ResponsiveInlineObjectsView(InlineObjectsView):
    template_name = 'forms/responsive_inline_objects.html'
