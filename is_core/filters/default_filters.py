from __future__ import unicode_literals

import re

from decimal import Decimal, InvalidOperation

from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.db.models import BooleanField, TextField, CharField, IntegerField, FloatField, Q
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField, ForeignKey
from django.db.models.fields import (AutoField, DateField, DateTimeField, DecimalField, GenericIPAddressField,
                                     IPAddressField)

from dateutil.parser import DEFAULTPARSER

from is_core.filters.exceptions import FilterException, FilterValueException

from chamber.utils.datetimes import make_aware


class Filter(object):

    def get_widget(self, *args, **kwargs):
        raise NotImplemented

    def get_q(self, value, request):
        raise NotImplemented

    def render(self, request):
        return ''


class DefaultFilter(Filter):
    suffixes = []
    default_suffix = None

    def __init__(self, filter_key, full_filter_key):
        self.filter_key = filter_key
        self.full_filter_key = full_filter_key
        self.is_exclude = False
        if self.filter_key.endswith('__not'):
            self.is_exclude = True
            self.filter_key = self.filter_key[:-5]
            self.full_filter_key = self.full_filter_key[:-5]

    def clean_value_with_suffix(self, value, suffix):
        return self.clean_value(value)

    def clean_value(self, value):
        return value

    @classmethod
    def get_suffixes(cls):
        return cls.suffixes

    def _check_suffix(self):
        if '__' in self.filter_key:
            suffix = self.filter_key.split('__', 1)[1]
            if suffix not in self.get_suffixes():
                raise FilterValueException(ugettext('Invalid operator {}.').format(suffix))
            return suffix
        else:
            return None

    def get_filter_term(self, value, suffix, request):
        raise NotImplementedError

    def get_q(self, value, request):
        suffix = self._check_suffix()
        value = self.clean_value_with_suffix(value, suffix)
        filter_term = self.get_filter_term(value, suffix, request)
        if isinstance(filter_term, dict):
            filter_term = Q(**filter_term)
        return ~Q(filter_term) if self.is_exclude else filter_term

    def get_filter_prefix(self):
        return self.full_filter_key[:-len(self.filter_key)]

    def get_filter_name(self):
        return self.get_full_filter_key()

    def get_default_suffix(self):
        return self.default_suffix

    def get_full_filter_key(self):
        full_filter_key = [self.full_filter_key]
        default_suffix = self.get_default_suffix()
        if default_suffix:
            full_filter_key.append(default_suffix)
        return '__'.join(full_filter_key)


class DefaultFieldOrMethodFilter(DefaultFilter):

    widget = None

    def get_filter_term(self, value, suffix, request):
        return {self.full_filter_key: value}

    def get_widget(self, request):
        return self.widget

    def get_placeholder(self, request):
        return None

    def get_attrs_for_widget(self):
        return {'data-filter': self.get_filter_name()}

    def render(self, request):
        widget = self.get_widget(request)
        placeholder = self.get_placeholder(request)
        if placeholder:
            widget.placeholder = placeholder
        return widget.render('filter__{}'.format(self.get_filter_name()), None,
                             attrs=self.get_attrs_for_widget())


class DefaultMethodFilter(DefaultFieldOrMethodFilter):

    def __init__(self, filter_key, full_filter_key, method):
        super(DefaultMethodFilter, self).__init__(filter_key, full_filter_key)
        self.method = method


class DefaultFieldFilter(DefaultFieldOrMethodFilter):

    suffixes = ['in', 'isnull']
    default_suffix = None
    ALL_LABEL = '--------'
    EMPTY_LABEL = _('Empty')
    ALL_SLUG = '__all__'
    EMPTY_SLUG = '__empty__'

    def __init__(self, filter_key, full_filter_key, field):
        super(DefaultFieldFilter, self).__init__(filter_key, full_filter_key)
        self.field = field

    def clean_value_with_suffix(self, value, suffix):
        if suffix == 'isnull':
            if value not in ['0', '1']:
                raise FilterValueException(ugettext('Value can be only "0" or "1"'))
            return value == '1'
        elif suffix == 'in':
            return self._parse_list_values(value)
        else:
            return self.clean_value(value)

    def clean_value(self, value):
        return value

    def get_widget(self, request):
        if self.widget:
            return self.widget

        formfield = self.field.formfield()
        if formfield:
            if hasattr(formfield, 'choices') and formfield.choices:
                formfield.choices = list(formfield.choices)
                if not formfield.choices[0][0]:
                    del formfield.choices[0]
                if self.field.null or self.field.blank:
                    formfield.choices.insert(0, (self.EMPTY_SLUG, self.EMPTY_LABEL))
                formfield.choices.insert(0, (self.ALL_SLUG, self.get_placeholder(request) or self.ALL_LABEL))
            return formfield.widget
        return forms.TextInput()

    def get_placeholder(self, request):
        return self.field.model._ui_meta.filter_placeholders.get(self.field.name, None)

    def get_attrs_for_widget(self):
        return {'data-filter': self.get_filter_name()}

    def _parse_list_values(self, value):
        for pattern in ('\[(.*)\]', '\((.*)\)', '\{(.*)\}'):
            m = re.compile(pattern).match(value)
            if m:
                return {self.clean_value(v) for v in m.group(1).split(',')} if m.group(1) else set()

        raise FilterValueException(
            ugettext('Value must be in list "[]", tuple "()" or set "{}" format split with char ",".')
        )

    def _filter_empty(self):
        return Q(**{'{}__isnull'.format(self.full_filter_key): True})

    def get_filter_term(self, value, suffix, request):
        if suffix == 'in':
            full_filter_key_without_suffix = self.full_filter_key.rsplit('__', 1)[0]
            if 'null' in value:
                value.remove('null')
                return (
                    Q(**{self.full_filter_key: value}) |
                    Q(**{'{}__isnull'.format(full_filter_key_without_suffix): True})
                )
        elif suffix == 'isnull':
            value = value == '1'
        elif not suffix:
            if value == self.ALL_SLUG:
                return {}
            if value == self.EMPTY_SLUG:
                return self._filter_empty()

        return {self.full_filter_key: value}


class CharFieldFilter(DefaultFieldFilter):

    suffixes = ['startswith', 'endswith', 'contains', 'icontains', 'in', 'isnull']
    default_suffix = 'icontains'

    def _filter_empty(self):
        return super(CharFieldFilter, self)._filter_empty() | Q(**{'{}__exact'.format(self.full_filter_key): ''})


class TextFieldFilter(CharFieldFilter):

    def get_widget(self, request):
        return forms.TextInput()


class BooleanFieldFilter(DefaultFieldFilter):

    def clean_value(self, value):
        if value not in ['0', '1']:
            raise FilterValueException(ugettext('Value can be only "0" or "1"'))
        return value == '1'

    def get_widget(self, request):
        return forms.Select(choices=(('', '-----'), (1, ugettext('Yes')), (0, ugettext('No'))))


class NumberFieldFilter(DefaultFieldFilter):

    suffixes = ['gt', 'lt', 'gte', 'lte', 'in', 'isnull']


class IntegerNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value):
        try:
            return int(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be integer.'.format(value)))


class FloatNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value):
        try:
            return float(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be float.'.format(value)))


class DecimalNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value):
        try:
            return Decimal(value)
        except InvalidOperation:
            raise FilterValueException(ugettext('Value "{}" must be decimal.'.format(value)))


class RelatedFieldFilter(DefaultFieldFilter):

    def get_last_rel_field(self, field):
        if not field.is_relation:
            return field
        else:
            next_field = field.rel.to._meta.get_field(field.rel.field_name)
            return self.get_last_rel_field(next_field)


class ForeignObjectRelFilter(RelatedFieldFilter):

    def clean_value(self, value):
        try:
            return self.get_last_rel_field(self.field.field.model._meta.get_field(
                self.field.field.model._meta.pk.name)).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))


class ForeignKeyFilter(RelatedFieldFilter):

    def clean_value(self, value):
        try:
            return self.get_last_rel_field(self.field).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))


class ManyToManyFieldFilter(RelatedFieldFilter):

    suffixes = ['all', 'in', 'isnull']

    def clean_value(self, value):
        try:
            return self.get_last_rel_field(
                self.field.rel.to._meta.get_field(self.field.m2m_target_field_name())
            ).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))

    def clean_value_with_suffix(self, value, suffix):
        if suffix == 'all':
            return self._parse_list_values(value)
        else:
            return super(ManyToManyFieldFilter, self).clean_value_with_suffix(value, suffix)

    def get_filter_term(self, value, suffix, request):
        if suffix == 'all':
            filter_key = self.filter_key.rsplit('__', 1)[0]

            qs_obj_with_all_values = self.field.model.objects.all()
            for v in set(value):
                qs_obj_with_all_values = qs_obj_with_all_values.filter(**{filter_key: v})
            return {'{}pk__in'.format(self.get_filter_prefix()): qs_obj_with_all_values.values('pk')}
        else:
            return super(ManyToManyFieldFilter, self).get_filter_term(value, suffix, request)


class DateFilter(DefaultFieldFilter):

    comparators = ['gt', 'lt', 'gte', 'lte', 'in']
    extra_suffixes = ['day', 'month', 'year']

    def _parse_datetime(self, value):
        value = DEFAULTPARSER._parse(value, dayfirst='-' not in value)
        value = value[0] if isinstance(value, tuple) else value
        if value is None:
            raise ValueError
        return value

    @classmethod
    def get_suffixes(cls):
        suffixes = cls.comparators + cls.extra_suffixes
        return suffixes

    def clean_value_with_suffix(self, value, suffix):
        if suffix in self.extra_suffixes:
            try:
                return int(value)
            except ValueError:
                raise FilterValueException(ugettext('Value "{}" must be integer.'.format(value)))
        elif suffix:
            try:
                return make_aware(DEFAULTPARSER.parse(value, dayfirst='-' not in value))
            except ValueError:
                raise FilterValueException(ugettext('Value "{}" must be date date (ISO 8601).'.format(value)))
        else:
            return super(DefaultFieldFilter, self).clean_value_with_suffix(value, suffix)

    def clean_value(self, value):
        try:
            return self._parse_datetime(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be date date (ISO 8601).'.format(value)))

    def get_filter_term(self, value, suffix, request):
        if suffix:
            return super(DateFilter, self).get_filter_term(value, suffix, request)
        else:
            filter_term = {}
            for attr in self.extra_suffixes:
                date_val = getattr(value, attr)
                if date_val:
                    filter_term['__'.join((self.full_filter_key, attr))] = date_val
            return filter_term


class DateTimeFilter(DateFilter):

    extra_suffixes = ['day', 'month', 'year', 'hour', 'minute', 'second']

    def clean_value(self, value):
        try:
            return self._parse_datetime(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be date datetime (ISO 8601).'.format(value)))


BooleanField.filter = BooleanFieldFilter
TextField.filter = TextFieldFilter
CharField.filter = CharFieldFilter
IntegerField.filter = IntegerNumberFieldFilter
FloatField.filter = FloatNumberFieldFilter
DecimalField.filter = DecimalNumberFieldFilter
AutoField.filter = IntegerNumberFieldFilter
DateField.filter = DateFilter
DateTimeField.filter = DateTimeFilter
GenericIPAddressField.filter = CharFieldFilter
IPAddressField.filter = CharFieldFilter
ManyToManyField.filter = ManyToManyFieldFilter
ForeignKey.filter = ForeignKeyFilter
ForeignObjectRel.filter = ForeignObjectRelFilter
