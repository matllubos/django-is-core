from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

from is_core.utils import query_string_from_dict
from is_core.generic_views import DefaultCoreViewMixin
from django.utils.html import format_html
from django.db.models.fields import Field, CharField, TextField, BooleanField
from django import forms


class Header(object):

    def __init__(self, field_name, text, sortable, filter):
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


    def __unicode__(self):
        if isinstance(self.field, BooleanField):
            widget = forms.Select(choices=((None, '-----'), (1, _('Yes')), (0, _('No'))))
        else:
            widget = self.field.formfield().widget
        return widget.render('filter__%s' % self.field_name, None, attrs={'data-filter': self.get_filter_name()})


class TableView(DefaultCoreViewMixin, TemplateView):
    list_display = ()
    template_name = 'generic_views/table.html'
    view_type = 'list'

    def __init__(self, core, site_name=None, menu_group=None, menu_subgroup=None, model=None, list_display=None):
        super(TableView, self).__init__(core, site_name, menu_group, menu_subgroup, model)
        self.list_display = self.list_display or list_display

    def get_title(self):
        return _('List %s') % self.model._meta.verbose_name

    def get_list_display(self):
        return self.list_display or self.core.get_list_display()

    def get_header(self, field_name):
        field = self.model._meta.get_field(field_name)
        return Header(field_name, field.verbose_name, True, Filter(field_name, field))

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
        info = self.site_name, '-'.join(self.core.get_menu_groups())
        context_data.update({
                                'headers': self.get_headers(),
                                'api_url_name': self.gel_api_url_name(),
                                'add_url_name': '%s:add-%s' % info,
                                'edit_url_name': '%s:edit-%s' % info,
                                'module_name': self.menu_subgroup,
                                'verbose_name':  self.model._meta.verbose_name,
                                'view_type': self.view_type,
                                'list_display': self.get_list_display(),
                                'list_action': self.core.get_list_actions(self.request),
                                'query_string_filter': self.get_query_string_filter()
                            })
        return context_data

    @classmethod
    def has_get_permission(cls, request, core, **kwargs):
        return core.has_read_permission(request)

