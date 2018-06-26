from is_core.generic_views.objects_views import ObjectsViewMixin
from is_core.generic_views.inlines import InlineView


class InlineObjectsView(ObjectsViewMixin, InlineView):
    """
    This inline class behaves and displays like 'InlineFormView', which is read-only. No need of any form or queryset.
    Implement method 'get_objects' and define a list of fields in the attribute 'fields'.
    """

    template_name = None


class TabularInlineObjectsView(InlineObjectsView):

    template_name = 'is_core/forms/tabular_inline_objects.html'


class ResponsiveInlineObjectsView(InlineObjectsView):

    template_name = 'is_core/forms/responsive_inline_objects.html'
