from django import forms
from django.views.generic.base import TemplateView
from django.urls import reverse

from pyston.filters.filters import OPERATORS

from is_core.auth.views import FieldPermissionViewMixin
from is_core.config import settings
from is_core.generic_views.base import DefaultModelCoreViewMixin
from is_core.rest.filters import UIFilterMixin, FilterChoiceIterator
from is_core.rest.datastructures import ModelFlatRestFields, ModelRestFieldset
from is_core.utils import (
    pretty_class_name, get_export_types_with_content_type, LOOKUP_SEP, get_field_label_from_path
)

from chamber.utils.http import query_string_from_dict

from pyston.filters.exceptions import FilterIdentifierError
from pyston.order.utils import DIRECTION
from pyston.order.exceptions import OrderIdentifierError
from pyston.serializer import get_resource_or_none


class Header:

    def __init__(self, field_name, text, order_by, filter_html=''):
        self.field_name = field_name
        self.text = text
        self.order_by = order_by
        self.filter = filter_html

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.text


class BaseModelTableViewMixin(FieldPermissionViewMixin):

    fields = None
    export_fields = None
    extra_fields = ('_obj_name', '_rest_links', '_actions', '_class_names', '_web_links', '_default_action')
    list_filter = None
    list_per_page = None
    model = None
    api_url = None
    menu_group_pattern_name = None
    render_actions = True
    enable_columns_manager = False
    field_labels = None

    title = None
    list_verbose_name = None
    verbose_name = None
    verbose_name_plural = None
    model_name = None

    def get_list_verbose_name(self):
        return self.list_verbose_name

    def get_verbose_name(self):
        return self.verbose_name

    def get_verbose_name_plural(self):
        return self.verbose_name_plural

    def get_model_name(self):
        return self.model_name

    def _get_allowed_fields(self):
        return [
            field for field in self._get_fields() if field not in self._get_disallowed_fields_from_permissions()
        ]

    def _get_allowed_extra_fields(self):
        return [
            field for field in self._get_extra_fields() if field not in self._get_disallowed_fields_from_permissions()
        ]

    def _get_allowed_export_fields(self):
        return [
            field for field in self._get_export_fields() if field not in self._get_disallowed_fields_from_permissions()
        ]

    def _get_field_filter_widget(self, filter_obj, full_field_name, field):
        return forms.TextInput()

    def _get_method_filter_widget(self, filter_obj, full_field_name, method):
        return forms.TextInput()

    def _get_resource_filter_widget(self, filter_obj, full_field_name):
        return forms.TextInput()

    def _get_filter_widget(self, filter_obj, full_field_name):
        if isinstance(filter_obj, UIFilterMixin):
            return filter_obj.get_widget(self.request)
        elif filter_obj.choices:
            return forms.Select(choices=FilterChoiceIterator(filter_obj.choices))
        elif filter_obj.field:
            return self._get_field_filter_widget(filter_obj, full_field_name, filter_obj.field)
        elif filter_obj.method:
            return self._get_method_filter_widget(filter_obj, full_field_name, filter_obj.method)
        else:
            return self._get_resource_filter_widget(filter_obj, full_field_name)

    def _get_filter_operator_string(self, filter_obj, widget):
        allowed_operators = filter_obj.get_allowed_operators()

        if isinstance(filter_obj, UIFilterMixin):
            return filter_obj.get_operator(widget).lower()
        if hasattr(widget, 'choices') and OPERATORS.EQ in allowed_operators:
            return OPERATORS.EQ
        else:
            return allowed_operators[0].lower()

    def _get_filter(self, field_name):
        resource = self.get_resource()
        if resource:
            try:
                return resource.filter_manager.get_filter(
                    field_name.split(LOOKUP_SEP), resource, self.request
                ) if resource else None
            except FilterIdentifierError:
                pass
        return None

    def _render_filter_object(self, field_name, filter_obj):
        widget = self._get_filter_widget(filter_obj, field_name)
        filter_term = LOOKUP_SEP.join((field_name, self._get_filter_operator_string(filter_obj, widget)))
        return widget.render('filter__{}'.format(filter_term), None, attrs={'data-filter': filter_term})

    def _render_filter(self, field_name):
        filter_obj = self._get_filter(field_name)
        return self._render_filter_object(field_name, filter_obj) if filter_obj else ''

    def _get_header_order_by(self, field_name):
        resource = self.get_resource()
        if resource:
            try:
                resource.order_manager.get_sorter(
                    field_name.split(LOOKUP_SEP), DIRECTION.ASC, resource, self.request
                )
                return field_name
            except OrderIdentifierError:
                return False
        else:
            return False

    def _get_field_labels(self):
        return self.field_labels

    def _get_paginator_type(self):
        resource = self.get_resource(self.model)
        if resource and resource.paginator:
            return resource.paginator.type
        else:
            return None

    def _get_header_label(self, field_name):
        return get_field_label_from_path(
            self.model, field_name, field_labels=self._get_field_labels()
        )

    def _get_header(self, field_name):
        return Header(
            field_name, self._get_header_label(field_name), self._get_header_order_by(field_name),
            self._render_filter(field_name)
        )

    def _get_fields(self):
        return () if self.fields is None else self.fields

    def _get_export_fields(self):
        return () if self.export_fields is None else self.export_fields

    def _get_extra_fields(self):
        return list(self.extra_fields)

    def _get_list_per_page(self):
        return settings.LIST_PER_PAGE if self.list_per_page is None else self.list_per_page

    def _generate_rest_fieldset(self):
        return ModelRestFieldset.create_from_flat_list(
            list(self._get_allowed_extra_fields()) + list(self._get_allowed_fields()),
            self.model
        )

    def _get_headers(self):
        headers = []
        for field in self._get_allowed_fields():
            if isinstance(field, (tuple, list)):
                headers.append(self._get_header(field[0]))
            else:
                headers.append(self._get_header(field))
        return headers

    def _get_api_url(self):
        return self.api_url

    def _get_list_filter(self):
        return {} if self.list_filter is None else self.list_filter

    def _prepare_filter_val(self, val):
        if isinstance(val, bool):
            return 1 if val else 0
        else:
            return val

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
        context_data = super().get_context_data(**kwargs)

        context_data.update({
            'headers': self._get_headers(),
            'api_url': self._get_api_url(),
            'module_name': self.get_model_name(),
            'fields': self._get_allowed_fields(),
            'rest_fieldset': self._generate_rest_fieldset(),
            'query_string_filter': self._get_query_string_filter(),
            'menu_group_pattern_name': self._get_menu_group_pattern_name(),
            'render_actions': self.render_actions,
            'enable_columns_manager': self.is_columns_manager_enabled(),
            'table_slug': self.get_table_slug(),
            'list_per_page': self._get_list_per_page(),
            'paginator_type': self._get_paginator_type(),
        })
        return context_data

    def is_columns_manager_enabled(self):
        return self.enable_columns_manager

    def get_table_slug(self):
        return pretty_class_name(self.__class__.__name__)

    def get_resource(self, model=None):
        return get_resource_or_none(self.request, model or self.model)


class DjangoTableViewMixin(BaseModelTableViewMixin):

    def _render_filter_object(self, field_name, filter_obj):
        if (filter_obj and not filter_obj.identifiers_suffix and filter_obj.field and filter_obj.field.is_relation and
                filter_obj.field.related_model and filter_obj.field.related_model._ui_meta.default_ui_filter_by):
            return self._render_filter(LOOKUP_SEP.join((
                field_name, filter_obj.field.related_model._ui_meta.default_ui_filter_by
            )))
        else:
            return super()._render_filter_object(field_name, filter_obj)

    def _get_field_filter_widget(self, filter_obj, full_field_name, field):
        formfield = field.formfield() if hasattr(field, 'formfield') else None
        if formfield:
            widget = formfield.widget
            if hasattr(widget, 'choices'):
                widget.choices = FilterChoiceIterator(widget.choices, field)

            if not isinstance(widget, forms.widgets.Textarea):
                return widget

        return forms.TextInput()

    def get_model_name(self):
        return str(self.model._meta.model_name)

    def get_list_verbose_name(self):
        list_verbose_name = super().get_list_verbose_name()
        return self.model._ui_meta.list_verbose_name if list_verbose_name is None else list_verbose_name

    def get_verbose_name(self):
        verbose_name = super().get_verbose_name()
        return self.model._meta.verbose_name if verbose_name is None else verbose_name

    def get_verbose_name_plural(self):
        verbose_name_plural = super().get_verbose_name_plural()
        return self.model._meta.verbose_name_plural if verbose_name_plural is None else verbose_name_plural


class BaseModelTableView(DefaultModelCoreViewMixin, BaseModelTableViewMixin, TemplateView):

    template_name = 'is_core/generic_views/table.html'
    view_type = 'list'
    export_types = None
    add_button_verbose_name = None

    def get_title(self):
        return self.get_list_verbose_name() % {
            'verbose_name': self.get_verbose_name(),
            'verbose_name_plural': self.get_verbose_name_plural()
        }

    def get_add_button_verbose_name(self):
        return self.add_button_verbose_name

    def _get_field_labels(self):
        return self.field_labels if self.field_labels is not None else self.core.get_field_labels(self.request)

    def _get_fields(self):
        return self.core.get_list_fields(self.request) if self.fields is None else self.fields

    def _get_export_fields(self):
        return self.core.get_export_fields(self.request) if self.export_fields is None else self.export_fields

    def _get_export_types(self):
        return self.core.get_export_types(self.request) if self.export_types is None else self.export_types

    def _get_list_per_page(self):
        list_per_page = self.core.get_list_per_page(self.request)
        return list_per_page if list_per_page is not None else super()._get_list_per_page()

    def _get_api_url(self):
        return self.core.get_api_url(self.request) if self.api_url is None else self.api_url

    def _get_list_filter(self):
        return self.core.get_default_list_filter(self.request) if self.list_filter is None else self.list_filter

    def _get_add_url(self):
        return self.core.get_add_url(self.request)

    def _generate_rest_export_fieldset(self):
        return ModelFlatRestFields.create_from_flat_list(
            list(self._get_allowed_export_fields()), self.model
        )

    def is_bulk_change_enabled(self):
        return (
            hasattr(self.core, 'is_bulk_change_enabled') and self.core.is_bulk_change_enabled() and
            self.core.ui_patterns.get(self.core.get_bulk_change_url_name()).has_permission('get', self.request)
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'add_url': self._get_add_url(),
            'view_type': self.view_type,
            'add_button_value': self.get_add_button_verbose_name() % {
                'verbose_name': self.get_verbose_name(),
                'verbose_name_plural': self.get_verbose_name_plural()
            },
            'enable_bulk_change': self.is_bulk_change_enabled(),
            'bulk_change_snippet_name': self.get_bulk_change_snippet_name(),
            'bulk_change_form_url': self.get_bulk_change_form_url(),
        })
        if self._get_export_types() and self._get_allowed_export_fields():
            context_data.update({
                'rest_export_fieldset': self._generate_rest_export_fieldset(),
                'export_types': get_export_types_with_content_type(self._get_export_types()),
            })
        return context_data

    def get_bulk_change_snippet_name(self):
        return '-'.join(('default', self.core.menu_group, 'form'))

    def get_bulk_change_form_url(self):
        return (
            reverse(''.join(('IS:', self.core.get_bulk_change_url_name(), '-', self.core.menu_group)))
            if self.is_bulk_change_enabled() else None
        )

    def _get_menu_group_pattern_name(self):
        return self.core.get_menu_group_pattern_name()


class DjangoTableView(DjangoTableViewMixin, BaseModelTableView):

    def get_add_button_verbose_name(self):
        return (
            self.model._ui_meta.add_button_verbose_name
            if self.add_button_verbose_name is None else self.add_button_verbose_name
        )
