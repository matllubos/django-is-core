import django

from django.forms.widgets import DateInput, DateTimeInput, TimeInput, Widget
from django.forms.fields import (ImageField, FileField, Field, URLField, MultipleChoiceField, ChoiceField,
                                 NullBooleanField)

from is_core.forms.utils import add_class_name
from is_core.forms.widgets import (DragAndDropFileInput, ReadonlyWidget, URLReadonlyWidget,
                                   FileReadonlyWidget, FulltextSelectMultiple, NullBooleanReadonlyWidget)


def build_attrs(self, base_attrs, extra_attrs=None, **kwargs):
    """ Helper function for building an attribute dictionary. """
    attrs = dict(base_attrs, **kwargs)
    if extra_attrs:
        attrs.update(extra_attrs)
    if self.class_name:
        attrs = add_class_name(attrs, self.class_name)
    if self.placeholder:
        attrs['placeholder'] = self.placeholder
    return attrs


Widget.placeholder = None
Widget.class_name = None
Widget.build_attrs = build_attrs

DateInput.class_name = 'date'
TimeInput.class_name = 'time'
DateTimeInput.class_name = 'datetime'

FileField.widget = DragAndDropFileInput
ImageField.widget = DragAndDropFileInput
MultipleChoiceField.widget = FulltextSelectMultiple

Field.is_readonly = False
Field.readonly_widget = ReadonlyWidget
URLField.readonly_widget = URLReadonlyWidget
FileField.readonly_widget = FileReadonlyWidget
NullBooleanField.readonly_widget = NullBooleanReadonlyWidget
