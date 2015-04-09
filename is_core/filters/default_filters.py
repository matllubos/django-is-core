from __future__ import unicode_literals

import re

from django.utils.translation import ugettext_lazy as _
from django import forms
from django.db.models import BooleanField, TextField, CharField, IntegerField, FloatField, Q
from django.db.models.fields.related import RelatedField
from django.db.models.fields import AutoField, DateField, DateTimeField, DecimalField, GenericIPAddressField

from dateutil.parser import DEFAULTPARSER

from is_core.filters.exceptions import FilterException


class Filter(object):

    def get_widget(self, *args, **kwargs):
        raise NotImplemented

    def filter_queryset(self, queryset, request):
        return queryset

    def render(self, request):
        return ''


class DefaultFilter(Filter):
    suffixes = []
    default_suffix = None
    widget = None

    def __init__(self, filter_key, full_filter_key, field_or_method, value=None):
        self.field_or_method = field_or_method
        self.filter_key = filter_key
        self.full_filter_key = full_filter_key
        self.value = value
        self.is_exclude = False
        if self.filter_key.endswith('__not'):
            self.is_exclude = True
            self.filter_key = self.filter_key[:-5]

    @classmethod
    def get_suffixes(cls):
        return cls.suffixes

    def _check_suffix(self):
        if '__' in self.filter_key:
            if self.filter_key.split('__', 1)[1] not in self.get_suffixes():
                raise FilterException(_('Not valid filter: %(filter_key)s=%(filter_value)s' %
                                        {'filter_key': self.full_filter_key, 'filter_value': self.value}))

    def get_filter_term(self, request):
        self._check_suffix()
        return {self.full_filter_key: self.value}

    def filter_queryset(self, queryset, request):
        filter_term = self.get_filter_term(request)
        if isinstance(filter_term, dict):
            filter_term = Q(**filter_term)
        if self.is_exclude:
            return queryset.exclude(filter_term)
        else:
            return queryset.filter(filter_term)

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

    def get_widget(self):
        return self.widget

    def render(self, request):
        widget = self.get_widget()
        if widget:
            return widget.render('filter__%s' % self.get_filter_name(), None,
                                 attrs={'data-filter': self.get_filter_name()})
        return ''


class DefaultFieldFilter(DefaultFilter):

    suffixes = []
    default_suffix = None
    EMPTY_LABEL = '---------'

    def __init__(self, filter_key, full_filter_key, field, value=None):
        super(DefaultFieldFilter, self).__init__(filter_key, full_filter_key, field, value)
        self.field = field

    def get_widget(self):
        if self.widget:
            return self.widget

        formfield = self.field.formfield()
        if formfield:
            if hasattr(formfield, 'empty_label'):
                formfield.empty_label = self.get_placeholder() or self.EMPTY_LABEL
            elif hasattr(formfield, 'choices') and formfield.choices and formfield.choices[0][0]:
                formfield.choices.insert(0, ('', self.get_placeholder() or self.EMPTY_LABEL))
            return formfield.widget
        return forms.TextInput()

    def get_placeholder(self):
        return self.field.model._ui_meta.filter_placeholders.get(self.field.name, '')

    def get_attrs_for_widget(self):
        attrs = {'data-filter': self.get_filter_name()}
        return attrs

    def render(self, request):
        widget = self.get_widget()
        placeholder = self.get_placeholder()
        if placeholder:
            widget.placeholder = placeholder
        return widget.render('filter__%s' % self.get_filter_name(), None,
                                        attrs=self.get_attrs_for_widget())


class CharFieldFilter(DefaultFieldFilter):

    suffixes = ['startswith', 'endswith', 'contains', 'icontains']
    default_suffix = 'icontains'


class TextFieldFilter(CharFieldFilter):

    def get_widget(self):
        return forms.TextInput()


class BooleanFieldFilter(DefaultFieldFilter):

    def get_widget(self):
        return forms.Select(choices=(('', '-----'), (1, _('Yes')), (0, _('No'))))


class NunberFieldFilter(DefaultFieldFilter):

    suffixes = ['gt', 'lt', 'gte', 'lte']


class RelatedFieldFilter(DefaultFieldFilter):

    suffixes = ['in']

    def get_widget(self):
        """ Turn off extra fields return """
        widget = super(RelatedFieldFilter, self).get_widget()
        return widget

    def get_filter_term(self, request):
        if '__' not in self.filter_key:
            return super(RelatedFieldFilter, self).get_filter_term(request)

        self._check_suffix()
        key, suffix = self.filter_key.split('__', 1)
        if suffix in 'in':
            p = re.compile('\[(.+)\]')
            m = p.match(self.value)
            if not m:
                raise ValueError()
            value = set(m.group(1).split(','))
            if 'null' in value:
                value.remove('null')
                return (Q(**{self.full_filter_key: value}) | Q(**{'%s__isnull' % key: True}))

            return {self.full_filter_key: value}
        else:
            return super(RelatedFieldFilter, self).get_filter_term(request)


class DateFilter(DefaultFieldFilter):

    comparators = ['gt', 'lt', 'gte', 'lte']
    extra_suffixes = ['day', 'month', 'year']

    @classmethod
    def get_suffixes(cls):
        suffixes = cls.comparators + cls.extra_suffixes
        return suffixes

    def get_filter_term(self, request):
        splitted_filter_key = self.filter_key.split('__')

        if len(splitted_filter_key) == 2 and splitted_filter_key[1] in self.comparators:
            if splitted_filter_key[1] in self.comparators:
                value = DEFAULTPARSER.parse(self.value, dayfirst=True)
                return {self.filter_key: value}
            else:
                return super(DateFilter, self).get_filter_term(request)

        parse = DEFAULTPARSER._parse(self.value, dayfirst=True)
        if parse is None:
            raise ValueError()
        res = parse[0] if isinstance(parse, tuple) else parse
        filter_terms = {}

        for attr in self.extra_suffixes:
            value = getattr(res, attr)
            if value:
                filter_terms['__'.join((self.filter_key, attr))] = value
        return filter_terms


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
