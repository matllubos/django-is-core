import django
from django import forms
from django.db.models.fields import FieldDoesNotExist
from django.forms.forms import pretty_name
from django.views.generic.base import TemplateView

from pyston.filters.default_filters import OPERATORS

from is_core.config import settings
from is_core.filters import UIFilterMixin, FilterChoiceIterator
from is_core.generic_views import DefaultModelCoreViewMixin
from is_core.rest.datastructures import ModelFlatRESTFields, ModelRESTFieldset
from is_core.utils import pretty_class_name, get_export_types_with_content_type
from is_core.utils.compatibility import reverse

from chamber.utils import get_class_method
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


class TableViewMixin:

    fields = None
    extra_fields = ('_obj_name', '_rest_links', '_actions', '_class_names', '_web_links', '_default_action')
    list_filter = None
    list_per_page = None
    model = None
    api_url = None
    menu_group_pattern_name = None
    render_actions = True
    enable_columns_manager = False
    field_labels = None

    def get_title(self):
        return self.model._ui_meta.list_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural}

    def _get_field_filter_widget(self, filter_obj, full_field_name, field):
        if filter_obj.choices:
            return forms.Select(choices=FilterChoiceIterator(filter_obj.choices))
        else:
            formfield = field.formfield() if hasattr(field, 'formfield') else None
            if formfield:
                widget = formfield.widget
                if hasattr(widget, 'choices'):
                    widget.choices = FilterChoiceIterator(widget.choices, field)

                if not isinstance(widget, forms.widgets.Textarea):
                    return widget

            return forms.TextInput()

    def _get_method_filter_widget(self, filter_obj, full_field_name, method):
        if filter_obj.choices:
            return forms.Select(choices=FilterChoiceIterator(filter_obj.choices))
        else:
            return forms.TextInput()

    def _get_resource_filter_widget(self, filter_obj, full_field_name):
        if filter_obj.choices:
            return forms.Select(choices=FilterChoiceIterator(filter_obj.choices))
        else:
            return forms.TextInput()

    def _get_filter_widget(self, filter_obj, full_field_name):
        if isinstance(filter_obj, UIFilterMixin):
            return filter_obj.get_widget(self.request)
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

    def _get_filter(self, full_field_name):
        resource = self.get_resource()
        if resource:
            try:
                filter_obj = resource.filter_manager.get_filter(full_field_name.split('__'), resource, self.request)
                if (not filter_obj.identifiers_suffix and filter_obj.field and filter_obj.field.is_relation and
                        filter_obj.field.related_model and
                        filter_obj.field.related_model._ui_meta.default_ui_filter_by):
                    return self._get_filter('{}__{}'.format(
                        full_field_name, filter_obj.field.related_model._ui_meta.default_ui_filter_by)
                    )
                widget = self._get_filter_widget(filter_obj, full_field_name)
                operator = self._get_filter_operator_string(filter_obj, widget)
                filter_term = '{}__{}'.format(full_field_name, operator)
                name = 'filter__{}'.format(filter_term)
                return widget.render(name, None, attrs={'data-filter': filter_term})
            except FilterIdentifierError:
                pass
        return ''

    def _get_header_order_by(self, model, full_field_name):
        resource = self.get_resource()
        if resource:
            try:
                resource.order_manager.get_sorter(full_field_name.split('__'), DIRECTION.ASC, resource, self.request)
                return full_field_name
            except OrderIdentifierError:
                return False
        else:
            return False

    def _get_field_labels(self):
        return self.field_labels

    def _get_header_label(self, model, full_field_name, field_name):
        field_labels = self._get_field_labels()

        if field_labels and full_field_name in field_labels:
            return field_labels.get(full_field_name)
        else:
            try:
                field = model._meta.get_field(field_name)
                if field.auto_created and (field.one_to_many or field.many_to_many):
                    return (
                        getattr(field.field, 'reverse_verbose_name', None) or
                        field.related_model._meta.verbose_name_plural
                    )
                elif field.auto_created and field.one_to_one:
                    return (
                        getattr(field.field, 'reverse_verbose_name', None) or
                        field.related_model._meta.verbose_name
                    )
                else:
                    return field.verbose_name
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
            return self._get_header(
                full_field_name, next_field_name, model._meta.get_field(current_field_name).related_model
            )

        return Header(
            full_field_name, self._get_header_label(model, full_field_name, field_name),
            self._get_header_order_by(model, full_field_name), self._get_filter(full_field_name)
        )

    def _get_fields(self):
        return () if self.fields is None else self.fields

    def _get_extra_fields(self):
        return list(self.extra_fields)

    def _get_list_per_page(self):
        return settings.LIST_PER_PAGE if self.list_per_page is None else self.list_per_page

    def _generate_rest_fieldset(self):
        return ModelRESTFieldset.create_from_flat_list(
            list(self._get_extra_fields()) + list(self._get_fields()),
            self.model
        )

    def _get_headers(self):
        headers = []
        for field in self._get_fields():
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
        context_data = super(TableViewMixin, self).get_context_data(**kwargs)

        if django.VERSION < (1, 7):
            module_name = str(self.model._meta.module_name)
        else:
            module_name = str(self.model._meta.model_name)

        context_data.update({
            'headers': self._get_headers(),
            'api_url': self._get_api_url(),
            'module_name': module_name,
            'fields': self._get_fields(),
            'rest_fieldset': self._generate_rest_fieldset(),
            'query_string_filter': self._get_query_string_filter(),
            'menu_group_pattern_name': self._get_menu_group_pattern_name(),
            'render_actions': self.render_actions,
            'enable_columns_manager': self.is_columns_manager_enabled(),
            'table_slug': self.get_table_slug(),
            'list_per_page': self._get_list_per_page(),
        })
        return context_data

    def is_columns_manager_enabled(self):
        return self.enable_columns_manager

    def get_table_slug(self):
        return pretty_class_name(self.__class__.__name__)

    def get_resource(self):
        return get_resource_or_none(self.request, self.model)


class TableView(TableViewMixin, DefaultModelCoreViewMixin, TemplateView):

    template_name = 'is_core/generic_views/table.html'
    view_type = 'list'
    export_types = None
    export_fields = None

    def _get_field_labels(self):
        return self.field_labels if self.field_labels is not None else self.core.get_ui_list_field_labels(self.request)

    def _get_fields(self):
        return self.core.get_ui_list_fields(self.request) if self.fields is None else self.fields

    def _get_export_fields(self):
        return self.core.get_ui_list_export_fields(self.request) if self.export_fields is None else self.export_fields

    def _get_export_types(self):
        return self.core.get_ui_list_export_types(self.request) if self.export_types is None else self.export_types

    def _get_list_per_page(self):
        return (
            self.core.get_list_per_page(self.request) or settings.LIST_PER_PAGE
            if self.list_per_page is None else self.list_per_page
        )

    def _get_api_url(self):
        return self.core.get_api_url(self.request) if self.api_url is None else self.api_url

    def _get_list_filter(self):
        return self.core.get_default_list_filter(self.request) if self.list_filter is None else self.list_filter

    def _get_add_url(self):
        return self.core.get_add_url(self.request)

    def _generate_rest_export_fieldset(self):
        return ModelFlatRESTFields.create_from_flat_list(
            list(self._get_export_fields()), self.model
        )

    def is_bulk_change_enabled(self):
        return hasattr(self.core, 'get_bulk_change_url_name') and self.core.get_bulk_change_url_name()

    def get_context_data(self, **kwargs):
        context_data = super(TableView, self).get_context_data(**kwargs)
        context_data.update({
            'add_url': self._get_add_url(),
            'view_type': self.view_type,
            'add_button_value': self.core.model._ui_meta.add_button_verbose_name % {
                'verbose_name': self.core.model._meta.verbose_name,
                'verbose_name_plural': self.core.model._meta.verbose_name_plural},
            'enable_bulk_change': self.is_bulk_change_enabled(),
            'bulk_change_snippet_name': self.get_bulk_change_snippet_name(),
            'bulk_change_form_url': self.get_bulk_change_form_url(),
        })
        if self._get_export_types() and self._get_export_fields():
            context_data.update({
                'rest_export_fieldset': self._generate_rest_export_fieldset(),
                'export_types': get_export_types_with_content_type(self._get_export_types()),
            })
        return context_data

    def get_bulk_change_snippet_name(self):
        return '-'.join(('default', self.model._meta.object_name.lower(), 'form'))

    def get_bulk_change_form_url(self):
        return (reverse(
            ''.join(('IS:', self.core.get_bulk_change_url_name(), '-', self.model._meta.object_name.lower())))
            if self.is_bulk_change_enabled() else None)

    def has_get_permission(self, **kwargs):
        return self.core.has_ui_read_permission(self.request)

    def _get_menu_group_pattern_name(self):
        return self.core.get_menu_group_pattern_name()
