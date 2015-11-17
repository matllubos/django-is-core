from __future__ import unicode_literals

import django

from django.views.generic.base import TemplateView
from django.db.models.fields import FieldDoesNotExist
from django.forms.forms import pretty_name
from django.utils.encoding import python_2_unicode_compatible

from chamber.utils import get_class_method

from is_core.generic_views import DefaultModelCoreViewMixin
from is_core.filters import get_model_field_or_method_filter
from is_core.rest.datastructures import ModelRESTFieldset, ModelFlatRESTFields
from is_core.filters.default_filters import *

from chamber.utils.http import query_string_from_dict


@python_2_unicode_compatible
class Header(object):

    def __init__(self, field_name, text, order_by, filter=''):
        self.field_name = field_name
        self.text = text
        self.order_by = order_by
        self.filter = filter

    def __str__(self):
        return self.text


class TableViewMixin(object):
    list_display = ()
    export_display = ()
    list_display_extra = ('_obj_name', '_rest_links', '_actions', '_class_names', '_web_links', '_default_action')
    list_filter = None
    model = None
    api_url = ''
    menu_group_pattern_name = None
    render_actions = True

    def get_title(self):
        return self.model._ui_meta.list_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural}

    def _get_filter(self, full_field_name):
        try:
            return get_model_field_or_method_filter(full_field_name, self.model).render(self.request)
        except FilterException:
            return ''

    def _full_field_name_prefix(self, full_field_name):
        if '__' in full_field_name:
            return full_field_name.rsplit('__', 1)
        else:
            return ''

    def _get_header_order_by(self, model, full_field_name):
        if '__' in full_field_name:
            prefix, field_name = full_field_name.rsplit('__', 1)
        else:
            prefix, field_name = '', full_field_name

        try:
            field = model._meta.get_field(field_name)
            default_order_by = full_field_name
        except FieldDoesNotExist:
            field = get_class_method(model, field_name)
            default_order_by = False

        order_by = getattr(field, 'order_by', None)
        if order_by:
            return '__'.join(filter(None, (prefix, order_by)))

        if order_by is None:
            return default_order_by

        return order_by

    def _get_header_label(self, model, field_name):
        try:
            return model._meta.get_field(field_name).verbose_name
        except FieldDoesNotExist:
            method = get_class_method(model, field_name)
            return getattr(method, 'short_description', pretty_name(field_name))

    def _get_header(self, full_field_name, field_name=None, model=None):
        if not model:
            model = self.model

        if not field_name:
            field_name = full_field_name

        if field_name == '_obj_name':
            return Header(full_field_name, model._meta.verbose_name, False)

        if '__' in field_name:
            current_field_name, next_field_name = field_name.split('__', 1)
            return self._get_header(full_field_name, next_field_name, model._meta.get_field(current_field_name).rel.to)

        return Header(
            full_field_name, self._get_header_label(model, field_name),
            self._get_header_order_by(model, full_field_name
        ), self._get_filter(full_field_name))

    def _get_list_display(self):
        return self.list_display

    def _get_export_display(self):
        return self.export_display or self.list_display

    def _get_list_display_extra(self):
        return list(self.list_display_extra)

    def _generate_rest_fieldset(self):
        return ModelRESTFieldset.create_from_flat_list(
            list(self._get_list_display_extra()) + list(self._get_list_display()), self.model
        )

    def _generate_rest_export_fieldset(self):
        return ModelFlatRESTFields.create_from_flat_list(
            list(self._get_export_display()), self.model
        )

    def _get_headers(self):
        headers = []
        for field in self._get_list_display():
            if isinstance(field, (tuple, list)):
                headers.append(self._get_header(field[0]))
            else:
                headers.append(self._get_header(field))
        return headers

    def _get_api_url(self):
        return self.api_url

    def _get_list_filter(self):
        return self.list_filter or {}

    def _prepare_filter_val(self, val):
        return (1 if val else 0) if isinstance(val, bool) else val

    def _prepare_filter_vals(self, filter_vals):
        return {key: self._prepare_filter_val(val) for key, val in filter_vals.items()}

    def _get_query_string_filter(self):
        default_list_filter = self._get_list_filter()
        filter_vals = default_list_filter.get('filter', {}).copy()
        exclude_vals = default_list_filter.get('exclude', {}).copy()

        for key, val in exclude_vals.items():
            filter_vals[key + '__not'] = val

        return query_string_from_dict(self._prepare_filter_vals(filter_vals))

    def _get_menu_group_pattern_name(self):
        return self.menu_group_pattern_name

    def get_context_data(self, **kwargs):
        context_data = super(TableViewMixin, self).get_context_data(**kwargs)

        if django.VERSION < (1, 7):
            module_name = str(self.model._meta.module_name)
        else:
            module_name = str(self.model._meta.model_name)

        context_data.update({
            'headers': self._get_headers(),
            'api_url': self._get_api_url(),
            'module_name': module_name,
            'list_display': self._get_list_display(),
            'rest_fieldset': self._generate_rest_fieldset(),
            'rest_export_fieldset': self._generate_rest_export_fieldset(),
            'query_string_filter': self._get_query_string_filter(),
            'menu_group_pattern_name': self._get_menu_group_pattern_name(),
            'render_actions': self.render_actions,
        })
        return context_data


class TableView(TableViewMixin, DefaultModelCoreViewMixin, TemplateView):
    template_name = 'generic_views/table.html'
    view_type = 'list'
    export_types = None

    def _get_list_display(self):
        return self.list_display or self.core.get_list_display(self.request)

    def _get_export_display(self):
        return self.export_display or self.core.get_export_display(self.request)

    def _get_export_types(self):
        return self.export_types or self.core.get_export_types(self.request)

    def _get_api_url(self):
        return self.api_url or self.core.get_api_url(self.request)

    def _get_list_filter(self):
        return self.list_filter or self.core.get_default_list_filter(self.request)

    def _get_add_url(self):
        return self.core.get_add_url(self.request)

    def get_context_data(self, **kwargs):
        context_data = super(TableView, self).get_context_data(**kwargs)
        context_data.update({
                                'add_url': self._get_add_url(),
                                'view_type': self.view_type,
                                'add_button_value': self.core.model._ui_meta.add_button_verbose_name %
                                                    {'verbose_name': self.core.model._meta.verbose_name,
                                                     'verbose_name_plural': self.core.model._meta.verbose_name_plural},
                                'export_types': self._get_export_types()
                            })
        return context_data

    def has_get_permission(self, **kwargs):
        return self.core.has_ui_read_permission(self.request)

    def _get_menu_group_pattern_name(self):
        return self.core.get_menu_group_pattern_name()
