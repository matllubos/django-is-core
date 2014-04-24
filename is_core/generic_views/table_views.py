from __future__ import unicode_literals

from django.views.generic.base import TemplateView
from django.db.models.fields import FieldDoesNotExist

from is_core.utils import query_string_from_dict
from is_core.generic_views import DefaultModelCoreViewMixin
from is_core.filters import get_model_field_or_method_filter

from is_core.filters.default_filters import *


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


class TableView(DefaultModelCoreViewMixin, TemplateView):
    list_display = ()
    template_name = 'generic_views/table.html'
    view_type = 'list'

    def __init__(self, core, site_name=None, menu_groups=None, model=None, list_display=None):
        super(TableView, self).__init__(core, site_name, menu_groups, model)
        self.list_display = self.list_display or list_display

    def get_title(self):
        return self.model._ui_meta.list_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural}

    def get_filter(self, full_field_name):
        try:
            return get_model_field_or_method_filter(full_field_name, self.model).render(self.request)
        except FilterException:
            return ''

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
            return Header(full_field_name, field.verbose_name, True, self.get_filter(full_field_name))
        except FieldDoesNotExist:
            return Header(full_field_name, getattr(getattr(model(), field_name), 'short_description', ''), False,
                          self.get_filter(full_field_name))

    def get_list_display(self):
        return self.list_display or self.core.get_ui_list_display(self.request)

    def get_headers(self):
        headers = []
        for field in self.get_list_display():
            if isinstance(field, (tuple, list)):
                headers.append(self.get_header(field[0]))
            else:
                headers.append(self.get_header(field))
        return headers

    def get_api_url(self):
        return self.core.get_api_url(self.request)

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
                                'api_url': self.get_api_url(),
                                'add_url': self.core.get_add_url(self.request),
                                'edit_url_name': '%s:edit-%s' % info,
                                'module_name': self.model._meta.module_name,
                                'verbose_name':  self.core.verbose_name_plural,
                                'view_type': self.view_type,
                                'list_display': self.get_list_display(),
                                'query_string_filter': self.get_query_string_filter(),
                                'menu_group_pattern_name': self.core.get_menu_group_pattern_name(),
                                'add_button_value': self.core.model._ui_meta.add_verbose_name %
                                                    {'verbose_name': self.core.model._meta.verbose_name,
                                                     'verbose_name_plural': self.core.model._meta.verbose_name_plural}
                            })
        return context_data

    @classmethod
    def has_get_permission(cls, request, **kwargs):
        return cls.core.has_read_permission(request)

    def bread_crumbs_menu_items(self):
        from is_core.templatetags.menu import LinkMenuItem

        menu_items = super(TableView, self).bread_crumbs_menu_items()
        menu_items.append(LinkMenuItem(self.get_title(), self.request.path, True))
        return menu_items
