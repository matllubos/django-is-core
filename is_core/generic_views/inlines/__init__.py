from django.views.generic.base import ContextMixin
from django.template.loader import render_to_string


class InlineView(ContextMixin):
    template_name = None

    def __init__(self, request, parent_view, parent_instance):
        self.request = request
        self.parent_view = parent_view
        self.parent_instance = parent_instance

    def render(self, context, title):
        template = self.template_name
        context.update(self.get_context_data(title=title))
        return render_to_string(template, context.flatten())

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self
