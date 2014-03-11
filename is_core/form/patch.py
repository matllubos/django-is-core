from django.forms.widgets import DateInput , DateTimeInput, TimeInput

from is_core.form.utils import add_class_name


def build_attrs(self, extra_attrs=None, **kwargs):
    super(self.__class__, self)
    attrs = super(self.__class__, self).build_attrs(extra_attrs, **kwargs)
    attrs = add_class_name(attrs, self.class_name)
    return attrs


DateInput.class_name = 'date'
TimeInput.class_name = 'time'
DateTimeInput.class_name = 'datetime'

DateInput.build_attrs = build_attrs
TimeInput.build_attrs = build_attrs
DateTimeInput.build_attrs = build_attrs
