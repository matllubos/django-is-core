from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import CharField, TextField, BooleanField, FieldDoesNotExist
from django import forms

from is_core.utils import query_string_from_dict
from is_core.generic_views import DefaultCoreViewMixin


class Header(object):

    def __init__(self, field_name, text, sortable, filter=''):
        self.field_name = field_name
        self.text = text
        self.sortable = sortable
        self.filter = filter

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.text


class Filter(object):

    def __init__(self, field_name, field):
        self.field_name = field_name
        self.field = field

    def get_filter_name(self):
        if isinstance(self.field, (CharField, TextField)):
            return '%s__contains' % self.field_name
        return self.field_name

    def get_widget(self):
        if isinstance(self.field, BooleanField):
            return forms.Select(choices=((None, '-----'), (1, _('Yes')), (0, _('No'))))
        elif isinstance(self.field, TextField):
            return forms.TextInput()
        elif self.field.formfield():
            return self.field.formfield().widget
        else:
            return forms.TextInput()

    def __unicode__(self):
        return self.get_widget().render('filter__%s' % self.field_name, None, attrs={'data-filter': self.get_filter_name()})


class TableView(DefaultCoreViewMixin, TemplateView):
    list_display = ()
    template_name = 'generic_views/table.html'
    view_type = 'list'

    def __init__(self, core, site_name=None, menu_groups=None, model=None, list_display=None):
        super(TableView, self).__init__(core, site_name, menu_groups, model)
        self.list_display = self.list_display or list_display

    def get_title(self):
        return _('List %s') % self.model._meta.verbose_name

    def get_header(self, full_field_name, field_name=None, model=None):
        if not model:
            model = self.model

        if not field_name:
            field_name = full_field_name

        if '__' in field_name:
            current_field_name, next_field_name = field_name.split('__', 1)
            return self.get_header(full_field_name, next_field_name, model._meta.get_field(current_field_name).rel.to)

        try:
            field = model._meta.get_field(field_name)
            return Header(full_field_name, field.verbose_name, True, Filter(full_field_name, field))
        except FieldDoesNotExist:
            return Header(full_field_name, getattr(model(), field_name).short_description, False)

    def get_list_display(self):
        return self.list_display or self.core.get_list_display()

    def get_headers(self):
        headers = []
        for field in self.get_list_display():
            if isinstance(field, (tuple, list)):
                headers.append(self.get_header(field[0]))
            else:
                headers.append(self.get_header(field))
        return headers

    def gel_api_url_name(self):
        return self.core.gel_api_url_name()

    def get_query_string_filter(self):
        default_list_filter = self.core.get_default_list_filter(self.request)

        filter_vals = default_list_filter.get('filter', {}).copy()
        exclude_vals = default_list_filter.get('exclude', {}).copy()

        for key, val in exclude_vals.items():
            filter_vals[key + '__not'] = val

        return query_string_from_dict(filter_vals)

    def get_context_data(self, **kwargs):
        context_data = super(TableView, self).get_context_data(**kwargs)
        info = self.site_name, self.core.get_menu_group_pattern_name()
        context_data.update({
                                'headers': self.get_headers(),
                                'api_url_name': self.gel_api_url_name(),
                                'add_url_name': '%s:add-%s' % info,
                                'edit_url_name': '%s:edit-%s' % info,
                                'module_name': self.model._meta.module_name,
                                'verbose_name':  self.model._meta.verbose_name,
                                'view_type': self.view_type,
                                'list_display': self.get_list_display(),
                                'list_action': self.core.get_list_actions(self.request),
                                'query_string_filter': self.get_query_string_filter(),
                                'menu_group_pattern_name': self.core.get_menu_group_pattern_name(),
                            })
        return context_data

    @classmethod
    def has_get_permission(cls, request, core, **kwargs):
        return core.has_read_permission(request)

