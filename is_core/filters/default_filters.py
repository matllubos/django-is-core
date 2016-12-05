from __future__ import unicode_literals

import re

from django.utils.translation import ugettext_lazy as _
from django import forms
from django.db.models import BooleanField, TextField, CharField, IntegerField, FloatField, Q
from django.db.models.fields.related import RelatedField, ManyToManyField
from django.db.models.fields import (AutoField, DateField, DateTimeField, DecimalField, GenericIPAddressField,
                                     IPAddressField)
from django.utils.timezone import make_aware, get_current_timezone

from dateutil.parser import DEFAULTPARSER

from is_core.filters.exceptions import FilterException, FilterValueException


class Filter(object):

    def get_widget(self, *args, **kwargs):
        raise NotImplemented

    def get_q(self, queryset, request):
        return queryset

    def render(self, request):
        return ''


class DefaultFilter(Filter):
    suffixes = []
    default_suffix = None

    def __init__(self, filter_key, full_filter_key, value=None):
        self.filter_key = filter_key
        self.full_filter_key = full_filter_key
        self.value = value
        self.is_exclude = False
        if self.filter_key.endswith('__not'):
            self.is_exclude = True
            self.filter_key = self.filter_key[:-5]
            self.full_filter_key = self.full_filter_key[:-5]

    @classmethod
    def get_suffixes(cls):
        return cls.suffixes

    def _check_suffix(self):
        if '__' in self.filter_key:
            suffix = self.filter_key.split('__', 1)[1]
            if suffix not in self.get_suffixes():
                raise FilterException(_('Not valid filter: %(filter_key)s=%(filter_value)s' %
                                        {'filter_key': self.full_filter_key, 'filter_value': self.value}))
            return suffix

    def get_filter_term(self, request):
        raise NotImplementedError

    def get_q(self, request):
        filter_term = self.get_filter_term(request)
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

    def get_filter_term(self, request):
        self._check_suffix()

        return {self.full_filter_key: self.value}

    def get_widget(self, request):
        return self.widget

    def render(self, request):
        widget = self.get_widget(request)
        return widget.render('filter__%s' % self.get_filter_name(), None,
                             attrs={'data-filter': self.get_filter_name()}) if widget else ''


class DefaultMethodFilter(DefaultFieldOrMethodFilter):

    def __init__(self, filter_key, full_filter_key, method, value=None):
        super(DefaultMethodFilter, self).__init__(filter_key, full_filter_key, value=value)
        self.method = method


class DefaultFieldFilter(DefaultFieldOrMethodFilter):

    suffixes = ['in', 'isnull']
    default_suffix = None
    ALL_LABEL = '--------'
    EMPTY_LABEL = _('Empty')
    ALL_SLUG = '__all__'
    EMPTY_SLUG = '__empty__'

    def __init__(self, filter_key, full_filter_key, field, value=None):
        super(DefaultFieldFilter, self).__init__(filter_key, full_filter_key, value)
        self.field = field

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
        return self.field.model._ui_meta.filter_placeholders.get(self.field.name, '')

    def get_attrs_for_widget(self):
        return {'data-filter': self.get_filter_name()}

    def render(self, request):
        widget = self.get_widget(request)
        placeholder = self.get_placeholder(request)
        if placeholder:
            widget.placeholder = placeholder
        return widget.render('filter__%s' % self.get_filter_name(), None,
                             attrs=self.get_attrs_for_widget())

    def _parse_list_values(self, value):
        for pattern in ('\[(.*)\]', '\((.*)\)', '\{(.*)\}'):
            m = re.compile(pattern).match(value)
            if m:
                return set(m.group(1).split(',')) if m.group(1) else set()

        raise FilterValueException

    def _filter_empty(self):
        return Q(**{'%s__isnull' % self.full_filter_key: True})

    def get_filter_term(self, request):
        suffix = self._check_suffix()

        value = self.value
        if suffix == 'in':
            full_filter_key_without_suffix = self.full_filter_key.rsplit('__', 1)[0]
            value = self._parse_list_values(self.value)
            if 'null' in value:
                value.remove('null')
                return (Q(**{self.full_filter_key: value}) | Q(**{'%s__isnull' % full_filter_key_without_suffix: True}))
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
        return super(CharFieldFilter, self)._filter_empty() | Q(**{'%s__exact' % self.full_filter_key: ''})


class TextFieldFilter(CharFieldFilter):

    def get_widget(self, request):
        return forms.TextInput()


class BooleanFieldFilter(DefaultFieldFilter):

    def get_widget(self, request):
        return forms.Select(choices=(('', '-----'), (1, _('Yes')), (0, _('No'))))


class NunberFieldFilter(DefaultFieldFilter):

    suffixes = ['gt', 'lt', 'gte', 'lte', 'in', 'isnull']


class RelatedFieldFilter(DefaultFieldFilter):

    pass


class ManyToManyFieldFilter(RelatedFieldFilter):

    suffixes = ['all', 'in', 'isnull']

    def get_filter_term(self, request):
        suffix = self._check_suffix()

        if suffix == 'all':
            full_filter_key_without_suffix = self.full_filter_key.rsplit('__', 1)[0]
            return Q(*(Q(**{full_filter_key_without_suffix: value}) for value in self._parse_list_values(self.value)))
        else:
            super(ManyToManyFieldFilter, self).get_filter_term(request)


class DateFilter(DefaultFieldFilter):

    comparators = ['gt', 'lt', 'gte', 'lte']
    extra_suffixes = ['day', 'month', 'year']

    @classmethod
    def get_suffixes(cls):
        suffixes = cls.comparators + cls.extra_suffixes
        return suffixes

    def get_filter_term(self, request):
        suffix = self._check_suffix()

        if suffix in self.comparators:
            value = DEFAULTPARSER.parse(self.value, dayfirst='-' not in self.value)
            value = make_aware(value, get_current_timezone())
            return {self.full_filter_key: value}
        elif suffix:
            return super(DateFilter, self).get_filter_term(request)
        else:
            parse = DEFAULTPARSER._parse(self.value, dayfirst='-' not in self.value)
            if parse is None:
                raise ValueError()
            res = parse[0] if isinstance(parse, tuple) else parse

            filter_term = {}
            for attr in self.extra_suffixes:
                value = getattr(res, attr)
                if value:
                    filter_term['__'.join((self.full_filter_key, attr))] = value
            return filter_term


class DateTimeFilter(DateFilter):

    extra_suffixes = ['day', 'month', 'year', 'hour', 'minute', 'second']


BooleanField.filter = BooleanFieldFilter
TextField.filter = TextFieldFilter
CharField.filter = CharFieldFilter
IntegerField.filter = NunberFieldFilter
FloatField.filter = NunberFieldFilter
DecimalField.filter = NunberFieldFilter
RelatedField.filter = RelatedFieldFilter
AutoField.filter = NunberFieldFilter
DateField.filter = DateFilter
DateTimeField.filter = DateTimeFilter
GenericIPAddressField.filter = CharFieldFilter
IPAddressField.filter = CharFieldFilter
ManyToManyField.filter = ManyToManyFieldFilter
