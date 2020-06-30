import re
import warnings
import datetime

from collections import OrderedDict

import django
from django.forms.forms import DeclarativeFieldsMetaclass, Form
from django.forms.fields import FileField
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.functional import cached_property

from pyston.forms import RESTFormMixin

from .fields import SmartReadonlyField
from .widgets import SmartWidgetMixin
from .boundfield import ReadonlyBoundField, SmartBoundField


class SmartFormMetaclass(DeclarativeFieldsMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = super(SmartFormMetaclass, cls).__new__(cls, name, bases, attrs)

        base_readonly_fields = set(getattr(new_class, 'base_readonly_fields', ()))
        base_required_fields = set(getattr(new_class, 'base_required_fields', ()))

        opts = getattr(new_class, 'Meta', None)
        if opts:
            setattr(opts, 'fields_to_clean', getattr(opts, 'fields_to_clean', None))
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


class SmartFormMixin:

    def __init__(self, *args, **kwargs):
        super(SmartFormMixin, self).__init__(*args, **kwargs)
        self.readonly_fields = set(self.base_readonly_fields)
        self._pre_init_fields()
        for field_name, field in self.fields.items():
            if hasattr(self, '_init_{}'.format(field_name)):
                getattr(self, '_init_{}'.format(field_name))(field)
        self._init_fields()

    def _pre_init_fields(self):
        for required_field_name in self.base_required_fields:
            if required_field_name in self.fields:
                self.fields[required_field_name].required = True

    def _init_fields(self):
        pass

    def __getitem__(self, name):
        """"
        Returns a BoundField with the given name.
        """
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key '%s' not found in '%s'. Choices are: %s." % (
                    name,
                    self.__class__.__name__,
                    ', '.join(sorted(f for f in self.fields)),
                )
            )
        if name not in self._bound_fields_cache:
            self._bound_fields_cache[name] = self._get_bound_field(name, field)
        return self._bound_fields_cache[name]

    def _get_bound_field(self, name, field):
        if name in self.readonly_fields:
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

    def _get_filtered_fields_to_clean(self):
        return ((name, field) for name, field in self.fields.items()
                if self._get_fields_to_clean() is None or name in self._get_fields_to_clean())

    def _get_fields_to_clean(self):
        return self.Meta.fields_to_clean if hasattr(self, 'Meta') else None

    def _clean_fields(self):
        tmp_fields = self.fields
        self.fields = OrderedDict((
            (name, field) for name, field in self._get_filtered_fields_to_clean()
            if name not in self.readonly_fields
        ))
        super(SmartFormMixin, self)._clean_fields()
        self.fields = tmp_fields

    def _register_readonly_field(self, field_name):
        if field_name not in self.readonly_fields:
            self.readonly_fields.add(field_name)

    def _unregister_readonly_field(self, field_name):
        if field_name in self.readonly_fields:
            self.readonly_fields.remove(field_name)

    @cached_property
    def changed_data(self):
        tmp_fields = self.fields
        self.fields = OrderedDict((
            (name, field) for name, field in self.fields.items()
            if name not in self.readonly_fields
        ))
        changed_data = super(SmartFormMixin, self).changed_data
        self.fields = tmp_fields
        return changed_data


class SmartForm(SmartFormMixin, RESTFormMixin, Form, metaclass=SmartFormMetaclass):
    pass


def smartform_factory(request, form, readonly_fields=None, required_fields=None, exclude=None,
                      formreadonlyfield_callback=None, fields_to_clean=None, readonly=False):
    attrs = {}
    if exclude is not None:
        attrs['exclude'] = exclude
    if readonly_fields is not None:
        attrs['readonly_fields'] = readonly_fields
    if required_fields is not None:
        attrs['required_fields'] = required_fields
    if fields_to_clean is not None:
        attrs['fields_to_clean'] = fields_to_clean
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
