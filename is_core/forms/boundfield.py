from django.forms.forms import BoundField
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from .widgets import SmartWidgetMixin
from .utils import ReadonlyValue


class SmartBoundField(BoundField):

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """

        widget = widget or self.field.widget
        if self.field.localize:
            widget.is_localized = True
        attrs = attrs or {}
        attrs = self.build_widget_attrs(attrs, widget)
        if self.auto_id and 'id' not in widget.attrs:
            attrs.setdefault('id', self.html_initial_id if only_initial else self.auto_id)

        if isinstance(widget, SmartWidgetMixin) and hasattr(self.form, '_request'):
            return widget.smart_render(
                request=self.form._request,
                name=self.html_initial_name if only_initial else self.html_name,
                value=self.value(),
                initial_value=self.initial,
                form=self.form,
                attrs=attrs,
                renderer=self.form.renderer
            )
        else:
            return widget.render(
                name=self.html_initial_name if only_initial else self.html_name,
                value=self.value(),
                attrs=attrs,
                renderer=self.form.renderer
            )




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
