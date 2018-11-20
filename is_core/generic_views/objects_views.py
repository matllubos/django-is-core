from django.db.models import Model
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

from is_core.utils import display_object_data, display_for_value
from is_core.generic_views import DefaultCoreViewMixin


class DataRow(list):

    def __init__(self, values, class_names):
        super(DataRow, self).__init__(values)
        self.class_names = class_names


class ObjectsViewMixin:
    """
    This class behaves and displays like table bud data are reaonly. No need of any form or queryset.
    Implement method 'get_objects' and define a list of fields in the attribute 'fields'.
    """

    # Tuple of tuples. The tuple consists of key and value (which will be displayed in template)
    # For eg: (('company_name', _('Company name')), ('zip', _('ZIP code')), ('...', '...'))
    fields = ()
    obj_class_names = ()
    no_items_text = _('There are no items')

    def get_fields(self):
        return list(self.fields)

    def parse_object(self, obj):
        return obj

    def get_objects(self):
        """
        This method must return a queryset of models, dictionaries or any iterable objects.

        Dictionaries must have keys defined in the attribute 'fields'. For eg: {'company_name': 'ABC', 'zip': '44455'}

        Objects / models must have attributes defined in the attribute 'fields'. Or it may have a humanizing methods
        'get_attributename_humanized', for eg: method 'get_zip_hunanized'.
        """
        raise NotImplementedError

    def get_data_list(self, fields, objects):
        out = []
        for obj in objects:
            normalized_obj = self.parse_object(obj)
            out.append(DataRow([(field_name, self.get_data_object(field_name, normalized_obj))
                                for field_name, _ in self.get_fields()],
                               self.get_obj_class_names(obj)))
        return out

    def get_obj_class_names(self, obj):
        return list(self.obj_class_names)

    def get_data_object(self, field_name, obj):
        if isinstance(obj, Model):
            return display_object_data(obj, field_name, request=self.request)
        elif isinstance(obj, dict):
            return display_for_value(obj.get(field_name), request=self.request)
        else:
            raise NotImplementedError

    def get_header_list(self, fields):
        return self.get_fields()

    def get_class_names(self):
        return [self.__class__.__name__.lower(), ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'data_list': self.get_data_list(self.get_fields(), self.get_objects()),
            'header_list': self.get_header_list(self.get_fields()),
            'class_names': self.get_class_names(),
            'no_items_text': self.no_items_text
        })
        return context_data


class ObjectsView(ObjectsViewMixin, DefaultCoreViewMixin, TemplateView):

    template_name = 'is_core/generic_views/objects.html'
