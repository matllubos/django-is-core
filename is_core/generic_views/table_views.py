from django.views.generic.base import TemplateView

from is_core.utils import query_string_from_dict
from is_core.generic_views import DefaultCoreViewMixin


class Header(object):

    def __init__(self, text, sortable):
        self.text = text
        self.sortable = sortable

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.text


class TableView(DefaultCoreViewMixin, TemplateView):
    list_display = ()
    template_name = 'generic_views/table.html'
    view_type = 'list'

    def get_title(self):
        return _('List %s') % self.model._meta.verbose_name

    def get_list_display(self):
        return self.list_display

    def get_header(self, field):
        return Header(self.model._meta.get_field(field).verbose_name, True)

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
        info = self.site_name, self.menu_group, self.menu_subgroup
        context_data.update({
                                'headers': self.get_headers(),
                                'api_url_name': self.gel_api_url_name(),
                                'add_url_name': '%s:add-%s-%s' % info,
                                'edit_url_name': '%s:edit-%s-%s' % info,
                                'module_name': self.menu_subgroup,
                                'verbose_name':  self.model._meta.verbose_name,
                                'view_type': self.view_type,
                                'list_display': self.get_list_display(),
                                'list_action': self.core.get_list_actions(),
                                'query_string_filter': self.get_query_string_filter()
                            })
        return context_data
