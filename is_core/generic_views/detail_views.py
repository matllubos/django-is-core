from django.http.response import Http404
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.views.generic.base import TemplateView
from django.template import RequestContext

from chamber.shortcuts import get_object_or_none

from is_core.auth.views import FieldPermissionViewMixin
from is_core.auth.permissions import (
    PermissionsSet, CoreReadAllowed, CoreUpdateAllowed, CoreAllowed, DEFAULT_PERMISSION
)
from is_core.generic_views.base import DefaultModelCoreViewMixin
from is_core.utils import (
    get_readonly_field_data, get_export_types_with_content_type, GetMethodFieldMixin, display_for_value,
    get_fieldsets_without_disallowed_fields, get_inline_views_opts_from_fieldsets
)
from is_core.generic_views.mixins import ListParentMixin, GetDjangoObjectCoreViewMixin, GetModelObjectCoreViewMixin
from is_core.generic_views.inlines.inline_table_views import DjangoInlineTableView
from is_core.rest.datastructures import ModelFlatRestFields

from .form_views import DjangoCoreFormView


class DjangoDetailFormView(GetDjangoObjectCoreViewMixin, DjangoCoreFormView):

    template_name = 'is_core/generic_views/detail_form.html'
    form_template = 'is_core/forms/model_detail_form.html'
    view_type = 'detail'
    messages = {'success': _('The %(name)s "%(obj)s" was changed successfully.'),
                'error': _('Please correct the error below.')}
    pk_name = 'pk'

    permission = PermissionsSet(
        get=CoreReadAllowed() | CoreUpdateAllowed(),
        post=CoreUpdateAllowed(),
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    detail_verbose_name = None

    def get_detail_verbose_name(self):
        return self.model._ui_meta.detail_verbose_name if self.detail_verbose_name is None else self.detail_verbose_name

    def get_title(self):
        return (self.title or
                self.get_detail_verbose_name() % {
                    'verbose_name': self.model._meta.verbose_name,
                    'verbose_name_plural': self.model._meta.verbose_name_plural,
                    'obj': self.get_obj(True)
                })

    def is_readonly(self):
        return not self.has_permission('post')

    def link(self, arguments=None, **kwargs):
        if arguments is None:
            arguments = (self.kwargs[self.pk_name],)
        return super().link(arguments=arguments, **kwargs)

    # TODO: get_obj should not be inside core get_obj and _get_perm_obj_or_404 should have same implementation
    def _get_perm_obj_or_404(self, pk=None):
        """
        If is send parameter pk is returned object according this pk,
        else is returned object from get_obj method, but it search only inside filtered values for current user,
        finally if object is still None is returned according the input key from all objects.

        If object does not exist is raised Http404
        """
        if pk:
            obj = get_object_or_none(self.core.model, pk=pk)
        else:
            try:
                obj = self.get_obj(False)
            except Http404:
                obj = get_object_or_none(self.core.model, **self.get_obj_filters())
        if not obj:
            raise Http404
        return obj

    def _get_export_types(self):
        return self.core.get_export_types(self.request) if self.export_types is None else self.export_types

    def _get_export_fields(self):
        return list(self.core.get_export_fields(self.request, self.get_obj(True)))

    def _generate_rest_detail_export_fieldset(self):
        return ModelFlatRestFields.create_from_flat_list(self._get_export_fields(), self.model)

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super().get_context_data(
            form=form, inline_form_views=inline_form_views, **kwargs
        )
        if self._get_export_types() and self._get_export_fields():
            context_data.update({
                'export_types': get_export_types_with_content_type(self._get_export_types()),
                'rest_detail_export_fieldset': self._generate_rest_detail_export_fieldset(),
                'api_url': self.core.get_api_detail_url(self.request, self.get_obj(True))
            })
        return context_data


class ModelReadonlyDetailView(GetModelObjectCoreViewMixin, FieldPermissionViewMixin, GetMethodFieldMixin,
                              ListParentMixin, DefaultModelCoreViewMixin, TemplateView):

    template_name = 'is_core/generic_views/readonly_detail.html'

    permission = PermissionsSet(
        get=CoreReadAllowed(),
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    fields = None
    fieldsets = None
    field_labels = None
    view_type = 'readonly-detail'
    detail_verbose_name = None
    inline_views = None

    def get_inline_views(self):
        return self.inline_views

    def get_detail_verbose_name(self):
        return self.detail_verbose_name

    def get_prefix(self):
        return '-'.join((self.view_type, self.site_name, self.core.get_menu_group_pattern_name())).lower()

    def is_readonly(self):
        return True

    def get_fields(self):
        return (
            self.fields is not None and self.fields or
            self.core.get_fields(self.request, self.get_obj())
        )

    def get_fieldsets(self):
        return (
            self.fieldsets is not None and self.fieldsets or
            self.core.get_fieldsets(self.request)
        )

    def generate_fieldsets(self, obj):
        fieldsets = self.get_fieldsets()

        if fieldsets is None:
            fieldsets = [
                (None, {
                    'fields': self.get_fields() or []
                })
            ]
            for inline_view in self.get_inline_views() or ():
                inline_view_inst = (
                    inline_view(self.request, self, obj) if isinstance(inline_view, type) else inline_view
                )
                if inline_view_inst.can_render():
                    # Only inline view that can be rendered is added to formset
                    fieldsets.append((
                        inline_view_inst.get_title(), {
                            'inline_view': inline_view,
                            'inline_view_inst': inline_view_inst
                        }
                    ))
        else:
            inline_view_opts = get_inline_views_opts_from_fieldsets(fieldsets)
            for inline_view_opt in inline_view_opts:
                inline_view = inline_view_opt['inline_view']
                inline_view_inst = (
                    inline_view(self.request, self, obj) if isinstance(inline_view, type) else inline_view
                )
                if inline_view_inst.can_render():
                    # Only inline view that can be rendered is added to formset
                    inline_view_opt['inline_view_inst'] = inline_view_inst

        return get_fieldsets_without_disallowed_fields(
            self.request, fieldsets, self._get_disallowed_fields_from_permissions()
        )

    def _get_field_labels(self):
        return (
            self.field_labels if self.field_labels is not None else self.core.get_field_labels(self.request)
        )

    def _get_field_to_render(self, obj, field_name):
        value, label, widget = get_readonly_field_data(
            obj, field_name, self.request, view=self, field_labels=self._get_field_labels()
        )
        return field_name, label, display_for_value(value, request=self.request), None

    def _get_fieldset_to_render(self, fieldset_title, fieldset_data, obj):
        fields = [
            self._get_field_to_render(obj, field_name)
            for field_name in fieldset_data.get('fields', ())
        ]
        fieldsets = [
            self._get_fieldset_to_render(sub_fieldset_title, sub_fieldset_data, obj)
            for sub_fieldset_title, sub_fieldset_data in fieldset_data.get('fieldsets', ())
        ]

        inline_view = fieldset_data.get('inline_view_inst')
        rendered_inline_view = inline_view.render(RequestContext(self.request), fieldset_title) if inline_view else ''

        return {
            'title': fieldset_title,
            'fields': fields,
            'fieldsets': fieldsets,
            'class': fieldset_data.get('class'),
            'rendered_inline_view': rendered_inline_view
        }

    def _get_fieldsets_to_render(self):
        obj = self.get_obj()
        return [
            self._get_fieldset_to_render(fieldset_title, fieldset_data, obj)
            for fieldset_title, fieldset_data in self.generate_fieldsets(obj)
        ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'fieldsets': self._get_fieldsets_to_render()
        })
        return context_data


class DjangoReadonlyDetailView(GetDjangoObjectCoreViewMixin, ModelReadonlyDetailView):

    def get_detail_verbose_name(self):
        return self.model._ui_meta.detail_verbose_name if self.detail_verbose_name is None else self.detail_verbose_name


class DjangoRelatedCoreTableView(DjangoReadonlyDetailView):

    table_model = None

    @cached_property
    def inline_table_view(self):
        return type(
            self.__class__.__name__ + 'InlineTableView', (DjangoInlineTableView,), {'model': self.table_model}
        )

    def get_fieldsets(self):
        return (
            (None, {'inline_view': self.inline_table_view}),
        )
