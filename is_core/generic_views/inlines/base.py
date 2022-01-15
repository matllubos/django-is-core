from django.views.generic.base import ContextMixin
from django.template.loader import render_to_string

from is_core.auth.views import FieldPermissionViewMixin
from is_core.auth.permissions import AllowAny, FieldsSetPermission

from .permissions import RelatedCoreAllowed


class InlineView(ContextMixin):

    template_name = None

    permission = AllowAny()
    title = None

    def __init__(self, request, parent_view, parent_instance):
        self.request = request
        self.parent_view = parent_view
        self.parent_instance = parent_instance
        assert self.permission, 'Permissions must be set'

    def get_title(self):
        return self.title

    def can_render(self):
        return self.permission.has_permission('read', self.request, self)

    def render(self, context, title):
        assert self.can_render(), 'Inline view cannot be rendered'

        template = self.template_name
        context.update(self.get_context_data(title=title))
        return render_to_string(template, context.flatten())

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


class RelatedInlineView(FieldPermissionViewMixin, InlineView):

    permission = RelatedCoreAllowed()
    model = None

    def __init__(self, request, parent_view, parent_instance):
        super().__init__(request, parent_view, parent_instance)
        self.related_core = self._get_related_core()

    def _get_field_permissions(self):
        related_core = self._get_related_core()
        if self.field_permissions is not None:
            return self.field_permissions
        return self.related_core.field_permissions if related_core else FieldsSetPermission()

    def _get_related_core(self):
        from is_core.site import get_model_core

        return get_model_core(self.model)
