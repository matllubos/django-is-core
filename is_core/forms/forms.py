import re

from django.forms.forms import BoundField

from is_core.forms.fields import SmartReadonlyField
from is_core.forms.widgets import SmartWidgetMixin


def pretty_class_name(class_name):
    return re.sub(r'(\w)([A-Z])', r'\1-\2', class_name).lower()


class SmartBoundField(BoundField):

    is_readonly = False

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """
        if not widget:
            widget = self.field.widget

        if self.field.localize:
            widget.is_localized = True

        attrs = attrs or {}
        auto_id = self.auto_id
        if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
            if not only_initial:
                attrs['id'] = auto_id
            else:
                attrs['id'] = self.html_initial_id

        if not only_initial:
            name = self.html_name
        else:
            name = self.html_initial_name

        if isinstance(widget, SmartWidgetMixin):
            return widget.smart_render(self.form._request, name, self.value(), attrs=attrs)
        return widget.render(name, self.value(), attrs=attrs)

    @property
    def type(self):
        if self.is_readonly:
            return 'readonly'
        else:
            return pretty_class_name(self.field.widget.__class__.__name__)


class ReadonlyBoundField(SmartBoundField):

    is_readonly = True

    def __init__(self, form, field, name):
        if isinstance(field, SmartReadonlyField):
            field._set_val_and_label(form.instance)
        super(ReadonlyBoundField, self).__init__(form, field, name)

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        if not widget:
            widget = self.field.widget
        return super(ReadonlyBoundField, self).as_widget(self.form._get_readonly_widget(self.name, self.field,
                                                                                        widget), attrs, only_initial)

    def value(self):
        data = self.form.initial.get(self.name, self.field.initial)
        if callable(data):
            data = data()
        return self.field.prepare_value(data)
