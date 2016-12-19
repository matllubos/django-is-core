from __future__ import unicode_literals

import re

from decimal import Decimal, InvalidOperation

from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.db.models import Q
from django.db.models.fields import (AutoField, DateField, DateTimeField, DecimalField, GenericIPAddressField,
                                     IPAddressField, BooleanField, TextField, CharField, IntegerField, FloatField,
                                     SlugField, EmailField)
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField, ForeignKey

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

    def clean_value_with_suffix(self, value, suffix, request):
        return self.clean_value(value, request)

    def clean_value(self, value, request):
        return value

    @classmethod
    def get_suffixes(cls):
        return cls.suffixes

    @classmethod
    def get_suffixes_with_not(cls):
        suffixes = cls.get_suffixes()
        return set(suffixes) | {'not'} | {'{}__not'.format(suffix) for suffix in suffixes}

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
        value = self.clean_value_with_suffix(value, suffix, request)
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

    def get_filter_term(self, value, suffix, request):
        raise NotImplementedError


class DefaultMethodFilter(DefaultFieldOrMethodFilter):

    def __init__(self, filter_key, full_filter_key, method):
        super(DefaultMethodFilter, self).__init__(filter_key, full_filter_key)
        self.method = method

    def _add_prefix_to_term(self, term):
        prefix = self.get_filter_prefix()
        return {'{}{}'.format(prefix, k): v for k, v in term.items()}

    def get_filter_term(self, value, suffix, request):
        return self._add_prefix_to_term(self.get_filter_term_without_prefix(value, suffix, request))

    def get_filter_term_without_prefix(self, value, suffix, request):
        raise NotImplementedError


class BooleanFilterMixin(object):

    widget = forms.Select(choices=(('', '-----'), (1, _('Yes')), (0, _('No'))))

    def clean_value(self, value, request):
        if value in ['0', '1']:
            return value == '1'
        else:
            raise FilterValueException(ugettext('Value can be only "0" or "1".'))


class DateFilterMixin(object):

    comparators = ['gt', 'lt', 'gte', 'lte', 'in']
    extra_suffixes = ['day', 'month', 'year']

    def _parse_datetime_to_parts(self, value):
        value = DEFAULTPARSER._parse(value, dayfirst='-' not in value)
        value = value[0] if isinstance(value, tuple) else value
        if value is None:
            raise ValueError
        else:
            return value

    def _parse_integer(self, value):
        try:
            return int(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be integer.'.format(value)))

    def _parse_whole_datetime(self, value):
        try:
            datetime_value = DEFAULTPARSER.parse(value, dayfirst='-' not in value)
            return make_aware(datetime_value) if datetime_value.tzinfo is None else datetime_value
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be in format ISO 8601.'.format(value)))

    @classmethod
    def get_suffixes(cls):
        suffixes = cls.comparators + cls.extra_suffixes
        return suffixes

    def clean_value_with_suffix(self, value, suffix, request):
        if suffix in self.extra_suffixes:
            return self._parse_integer(value)
        elif suffix:
            return self._parse_whole_datetime(value)
        else:
            return super(DateFilterMixin, self).clean_value_with_suffix(value, suffix, request)

    def clean_value(self, value, request):
        try:
            return self._parse_datetime_to_parts(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be in format ISO 8601.'.format(value)))


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

    def clean_value_with_suffix(self, value, suffix, request):
        if suffix == 'isnull':
            if value not in ['0', '1']:
                raise FilterValueException(ugettext('Value can be only "0" or "1".'))
            return value == '1'
        elif suffix == 'in':
            return self._parse_list_values(value, request)
        elif value in self.get_extra_values():
            return value
        else:
            return self.clean_value(value, request)

    def get_extra_values(self):
        return {self.ALL_SLUG, self.EMPTY_SLUG}

    def clean_value(self, value, request):
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

    def _parse_list_values(self, value, request):
        for pattern in ('\[(.*)\]', '\((.*)\)', '\{(.*)\}'):
            m = re.compile(pattern).match(value)
            if m:
                return {self.clean_value(v, request) for v in m.group(1).split(',')} if m.group(1) else set()

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
        elif not suffix and value == self.ALL_SLUG:
            return {}
        elif not suffix and value == self.EMPTY_SLUG:
            return self._filter_empty()
        else:
            return {self.full_filter_key: value}


class CharFieldFilter(DefaultFieldFilter):

    suffixes = ['startswith', 'endswith', 'contains', 'icontains', 'in', 'isnull']

    def _filter_empty(self):
        return super(CharFieldFilter, self)._filter_empty() | Q(**{'{}__exact'.format(self.full_filter_key): ''})


class CaseSensitiveCharFieldFilter(CharFieldFilter):

    default_suffix = 'contains'


class CaseInsensitiveCharFieldFilter(CharFieldFilter):

    default_suffix = 'icontains'


class TextFieldFilter(CaseInsensitiveCharFieldFilter):

    def get_widget(self, request):
        return forms.TextInput()


class BooleanFieldFilter(BooleanFilterMixin, DefaultFieldFilter):

    pass


class NumberFieldFilter(DefaultFieldFilter):

    suffixes = ['gt', 'lt', 'gte', 'lte', 'in', 'isnull']


class IntegerNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value, request):
        try:
            return int(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be integer.'.format(value)))


class FloatNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value, request):
        try:
            return float(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" must be float.'.format(value)))


class DecimalNumberFieldFilter(NumberFieldFilter):

    def clean_value(self, value, request):
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

    suffixes = ['all', 'in', 'isnull']

    def get_widget(self, request):
        """
        Reverse relation cannot be uset as UI filter now. It is left as future work.
        """
        raise NotImplementedError

    def clean_value_with_suffix(self, value, suffix, request):
        if suffix == 'all':
            return self._parse_list_values(value, request)
        else:
            return super(ForeignObjectRelFilter, self).clean_value_with_suffix(value, suffix, request)

    def clean_value(self, value, request):
        try:
            return self.get_last_rel_field(
                self.field.related_model._meta.get_field(self.field.related_model._meta.pk.name)
            ).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))

    def get_filter_term(self, value, suffix, request):
        if suffix == 'all':
            filter_key = self.filter_key.rsplit('__', 1)[0]

            qs_obj_with_all_values = self.field.model.objects.all()
            for v in set(value):
                qs_obj_with_all_values = qs_obj_with_all_values.filter(**{filter_key: v})
            return {'{}pk__in'.format(self.get_filter_prefix()): qs_obj_with_all_values.values('pk')}
        else:
            return super(ForeignObjectRelFilter, self).get_filter_term(value, suffix, request)


class ForeignKeyFilter(RelatedFieldFilter):

    def clean_value(self, value, request):
        try:
            return self.get_last_rel_field(self.field).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))


class ManyToManyFieldFilter(RelatedFieldFilter):

    suffixes = ['all', 'in', 'isnull']

    def clean_value(self, value, request):
        try:
            return self.get_last_rel_field(
                self.field.rel.to._meta.get_field(self.field.m2m_target_field_name())
            ).get_prep_value(value)
        except ValueError:
            raise FilterValueException(ugettext('Value "{}" is invalid.'.format(value)))

    def clean_value_with_suffix(self, value, suffix, request):
        if suffix == 'all':
            return self._parse_list_values(value, request)
        else:
            return super(ManyToManyFieldFilter, self).clean_value_with_suffix(value, suffix, request)

    def get_filter_term(self, value, suffix, request):
        if suffix == 'all':
            filter_key = self.filter_key.rsplit('__', 1)[0]

            qs_obj_with_all_values = self.field.model.objects.all()
            for v in set(value):
                qs_obj_with_all_values = qs_obj_with_all_values.filter(**{filter_key: v})
            return {'{}pk__in'.format(self.get_filter_prefix()): qs_obj_with_all_values.values('pk')}
        else:
            return super(ManyToManyFieldFilter, self).get_filter_term(value, suffix, request)


class DateFilter(DateFilterMixin, DefaultFieldFilter):

    def get_filter_term(self, value, suffix, request):
        if suffix or value in self.get_extra_values():
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


BooleanField.default_filter = BooleanFieldFilter
TextField.default_filter = TextFieldFilter
CharField.default_filter = CaseInsensitiveCharFieldFilter
IntegerField.default_filter = IntegerNumberFieldFilter
FloatField.default_filter = FloatNumberFieldFilter
DecimalField.default_filter = DecimalNumberFieldFilter
AutoField.default_filter = IntegerNumberFieldFilter
DateField.default_filter = DateFilter
DateTimeField.default_filter = DateTimeFilter
GenericIPAddressField.default_filter = CaseSensitiveCharFieldFilter
IPAddressField.default_filter = CaseSensitiveCharFieldFilter
ManyToManyField.default_filter = ManyToManyFieldFilter
ForeignKey.default_filter = ForeignKeyFilter
ForeignObjectRel.default_filter = ForeignObjectRelFilter
SlugField.default_filter = CaseSensitiveCharFieldFilter
EmailField.default_filter = CaseSensitiveCharFieldFilter
