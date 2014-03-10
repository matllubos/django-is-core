from django.utils.translation import ugettext_lazy as _
from django import forms
from django.db.models import BooleanField, TextField, CharField, IntegerField, FloatField
from django.db.models.fields.related import RelatedField
from django.db.models.fields import AutoField, DateField, DateTimeField

from dateutil.parser import DEFAULTPARSER

from is_core.filters.exceptions import FilterException


class Filter(object):

    def get_widget(self, *args, **kwargs):
        raise NotImplemented

    def filter_queryset(self, queryset):
        return queryset

    def __unicode__(self):
        return ''


class DefaultFieldFilter(Filter):

    suffixes = []
    default_suffix = None

    def __init__(self, filter_key, full_filter_key, field, value=None):
        self.field = field
        self.filter_key = filter_key
        self.full_filter_key = full_filter_key
        self.value = value
        self.is_exclude = False
        if self.filter_key.endswith('__not'):
            self.is_exclude = True
            self.filter_key = self.filter_key[:-5]

    def get_filter_term(self):
        if '__' in self.filter_key:
            if self.filter_key.split('__', 1)[1] not in self.suffixes:
                raise FilterException(_('Not valid filter: %s=%s' % (self.full_filter_key, self.value)))
        return {self.filter_key: self.value}

    def filter_queryset(self, queryset):
        if self.is_exclude:
            return queryset.exclude(**self.get_filter_term())
        else:
            return queryset.filter(**self.get_filter_term())

    def get_widget(self):
        formfield = self.field.formfield()
        if formfield:
            return formfield.widget
        return forms.TextInput()

    def get_full_filter_key(self):
        full_filter_key = [self.full_filter_key]
        default_suffix = self.get_default_suffix()
        if default_suffix:
            full_filter_key.append(default_suffix)
        return '__'.join(full_filter_key)

    def get_default_suffix(self):
        return self.default_suffix

    def get_filter_name(self):
        return self.get_full_filter_key()

    def __unicode__(self):
        return self.get_widget().render('filter__%s' % self.get_filter_name(), None,
                                        attrs={'data-filter': self.get_filter_name()})


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


class DateFilter(DefaultFieldFilter):

    comparators = ['gt', 'lt', 'gte', 'lte']
    extra_suffixes = ['day', 'month', 'year']

    @property
    def suffixes(self):
        suffixes = self.comparators + self.extra_suffixes

        for suffix in self.extra_suffixes:
            for comparator in self.comparators:
                suffixes.append('__'.join((suffix, comparator)))

        return suffixes

    def get_filter_term(self):
        if '__' in self.filter_key:
            return super(DateTimeFilter, self).get_filter_term()

        res, _ = DEFAULTPARSER._parse(self.value)
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
RelatedField.filter = RelatedFieldFilter
AutoField.filter = NunberFieldFilter
DateField.filter = DateFilter
DateTimeField.filter = DateTimeFilter
