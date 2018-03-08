from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from is_core.utils.compatibility import BoundField

from .widgets import SmartWidgetMixin
from .utils import ReadonlyValue


class SmartBoundField(BoundField):

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
        attrs = self.build_widget_attrs(attrs, widget)
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
        if isinstance(widget, SmartWidgetMixin) and hasattr(self.form, '_request'):
            return force_text(widget.smart_render(self.form._request, name, self.value(), self.initial,
                                                  self.form, attrs=attrs))
        else:
            return force_text(widget.render(name, self.value(), attrs=attrs))


class ReadonlyBoundField(SmartBoundField):

    type = 'readonly'
    is_readonly = True

    def __init__(self, form, field, name):
        from .fields import SmartReadonlyField

        if isinstance(field, SmartReadonlyField):
            field._set_readonly_field(name, form)
        super(ReadonlyBoundField, self).__init__(form, field, name)

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        if not widget:
            widget = self.field.widget

        if widget.is_hidden:
            return mark_safe('')
        else:
            return super(ReadonlyBoundField, self).as_widget(
                self.form._get_readonly_widget(self.name, self.field, widget), attrs, only_initial
            )

    def as_hidden(self, attrs=None, **kwargs):
        """
        Returns a string of HTML for representing this as an <input type="hidden">.
        Because readonly has not hidden input there must be returned empty string.
        """
        return mark_safe('')

    @property
    def initial(self):
        data = self.form.initial.get(self.name, self.field.initial)
        if callable(data):
            data = data()

        value = self.field.prepare_value(data)

        if hasattr(self.form, 'humanized_data') and self.name in self.form.humanized_data:
            humanized_value = self.form.humanized_data.get(self.name)
            return ReadonlyValue(value, humanized_value)
        return value

    def value(self):
        return self.initial
