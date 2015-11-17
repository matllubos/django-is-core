from __future__ import unicode_literals

import re

from datetime import datetime, time

import django

from django.utils import six
from django.forms.forms import BoundField, DeclarativeFieldsMetaclass, Form
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text

from piston.forms import RESTFormMixin

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

        if isinstance(widget, SmartWidgetMixin) and hasattr(self.form, '_request'):
            return widget.smart_render(self.form._request, name, self.value(), self._form_initial_value(), attrs=attrs)
        return force_text(widget.render(name, self.value(), attrs=attrs))

    @property
    def type(self):
        if self.is_readonly:
            return 'readonly'
        else:
            return pretty_class_name(self.field.widget.__class__.__name__)

    def _bound_value(self):
        data = self.field.bound_data(
            self.data, self.form.initial.get(self.name, self.field.initial)
        )
        return self.field.prepare_value(data)

    def _form_initial_value(self):
        data = self.form.initial.get(self.name, self.field.initial)
        if callable(data):
            data = data()
            if django.VERSION > (1, 6):
                # If this is an auto-generated default date, nix the
                # microseconds for standardized handling. See #22502.
                if (isinstance(data, (datetime.datetime, datetime.time)) and
                        not getattr(self.field.widget, 'supports_microseconds', True)):
                    data = data.replace(microsecond=0)

        return self.field.prepare_value(data)

    def value(self):
        if not self.form.is_bound:
            return self._form_initial_value()
        else:
            return self._bound_value()


class ReadonlyValue(object):

    def __init__(self, value, humanized_value):
        self.value = value
        self.humanized_value = humanized_value


class ReadonlyBoundField(SmartBoundField):

    is_readonly = True

    def __init__(self, form, field, name):
        if isinstance(field, SmartReadonlyField):
            field._set_readonly_field(form.instance)
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

    def _form_initial_value(self):
        data = self.form.initial.get(self.name, self.field.initial)
        if callable(data):
            data = data()

        value = self.field.prepare_value(data)
        if hasattr(self.form, 'humanized_data') and self.name in self.form.humanized_data:
            humanized_value = self.form.humanized_data.get(self.name)
            return ReadonlyValue(value, humanized_value)
        return value

    def value(self):
        return self._form_initial_value()


class SmartFormMetaclass(DeclarativeFieldsMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = super(SmartFormMetaclass, cls).__new__(cls, name, bases, attrs)

        base_readonly_fields = set(getattr(new_class, 'base_readonly_fields', ()))
        base_required_fields = set(getattr(new_class, 'base_required_fields', ()))

        opts = getattr(new_class, 'Meta', None)
        if opts:
            exclude_fields = getattr(opts, 'exclude', None) or ()
            readonly_fields = getattr(opts, 'readonly_fields', None) or ()
            readonly = getattr(opts, 'readonly', None) or False
            required_fields = getattr(opts, 'required_fields', None) or ()

            for field_name, field in new_class.base_fields.items():
                if field_name in exclude_fields:
                    del new_class.base_fields[field_name]
                elif ((field_name in readonly_fields or readonly or field.is_readonly) and
                      field_name not in base_readonly_fields):
                    base_readonly_fields.add(field_name)
                elif field_name in required_fields and field_name not in base_required_fields:
                    base_required_fields.add(field_name)

            for field_name in set(readonly_fields):
                if (field_name not in new_class.base_fields and 'formreadonlyfield_callback' in attrs and
                    attrs['formreadonlyfield_callback'] is not None):
                    new_class.base_fields[field_name] = attrs['formreadonlyfield_callback'](field_name)
                    base_readonly_fields.add(field_name)

        new_class.base_readonly_fields = base_readonly_fields
        new_class.base_required_fields = base_required_fields
        return new_class


# TODO: check django version
class SmartFormMixin(object):

    def __init__(self, *args, **kwargs):
        super(SmartFormMixin, self).__init__(*args, **kwargs)
        self._pre_init_fields()
        for field_name, field in self.fields.items():
            if hasattr(self, '_init_%s' % field_name):
                getattr(self, '_init_%s' % field_name)(field)
        self._init_fields()

    def _pre_init_fields(self):
        for required_field_name in self.base_required_fields:
            if required_field_name in self.fields:
                self.fields[required_field_name].required = True

    def _init_fields(self):
        pass

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)

        if name in self.base_readonly_fields:
            return ReadonlyBoundField(self, field, name)
        else:
            return SmartBoundField(self, field, name)

    def _get_readonly_widget(self, field_name, field, widget):
        if field.readonly_widget:
            if isinstance(field.readonly_widget, type):
                return field.readonly_widget(widget)
            else:
                return field.readonly_widget
        return field.widget

    def _clean_fields(self):
        for name, field in self.fields.items():
            if name not in self.base_readonly_fields:
                # value_from_datadict() gets the data from the data dictionaries.
                # Each widget type knows how to retrieve its own data, because some
                # widgets split data over several HTML fields.
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                try:
                    if isinstance(field, FileField):
                        initial = self.initial.get(name, field.initial)
                        value = field.clean(value, initial)
                    else:
                        value = field.clean(value)
                    self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
                except ValidationError as e:
                    self._errors[name] = self.error_class(e.messages)
                    if name in self.cleaned_data:
                        del self.cleaned_data[name]

    def _register_readonly_field(self, field_name):
        if field_name not in self.base_readonly_fields:
            self.base_readonly_fields.append(field_name)

    def _unregister_readonly_field(self, field_name):
        if field_name in self.base_readonly_fields:
            self.base_readonly_fields.remove(field_name)

    @property
    def changed_data(self):
        if self._changed_data is None:
            self._changed_data = []
            # XXX: For now we're asking the individual widgets whether or not the
            # data has changed. It would probably be more efficient to hash the
            # initial data, store it in a hidden field, and compare a hash of the
            # submitted data, but we'd need a way to easily get the string value
            # for a given field. Right now, that logic is embedded in the render
            # method of each widget.
            for name, field in self.fields.items():
                if name not in self.base_readonly_fields:
                    prefixed_name = self.add_prefix(name)
                    data_value = field.widget.value_from_datadict(self.data, self.files, prefixed_name)
                    if not field.show_hidden_initial:
                        initial_value = self.initial.get(name, field.initial)
                        if callable(initial_value):
                            initial_value = initial_value()
                    else:
                        initial_prefixed_name = self.add_initial_prefix(name)
                        hidden_widget = field.hidden_widget()
                        try:
                            initial_value = field.to_python(hidden_widget.value_from_datadict(
                                self.data, self.files, initial_prefixed_name))
                        except ValidationError:
                            # Always assume data has changed if validation fails.
                            self._changed_data.append(name)
                            continue
                    if field._has_changed(initial_value, data_value):
                        self._changed_data.append(name)
        return self._changed_data


class SmartForm(six.with_metaclass(SmartFormMetaclass, SmartFormMixin, RESTFormMixin, Form)):
    pass


def smartform_factory(request, form, readonly_fields=None, required_fields=None, exclude=None,
                      formreadonlyfield_callback=None, readonly=False):
    attrs = {}
    if exclude is not None:
        attrs['exclude'] = exclude
    if readonly_fields is not None:
        attrs['readonly_fields'] = readonly_fields
    if required_fields is not None:
        attrs['required_fields'] = required_fields
    attrs['readonly'] = readonly
    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type(str('Meta'), parent, attrs)

    class_name = form.__name__

    form_class_attrs = {
        'Meta': Meta,
        'formreadonlyfield_callback': formreadonlyfield_callback,
        '_request': request,
    }

    form_class = type(form)(class_name, (form,), form_class_attrs)
    return form_class
