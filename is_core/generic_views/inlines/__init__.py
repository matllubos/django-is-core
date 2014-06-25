from django.views.generic.base import ContextMixin
from django.template.loader import render_to_string


class InlineView(ContextMixin):
    template_name = None

    def __init__(self, request, parent_view):
        self.request = request
        self.parent_view = parent_view

    def render(self, context, title):
        template = self.template_name
        print 'te'
        print self.get_context_data(title=title)
        context.update(self.get_context_data(title=title))
        return render_to_string(template, context)
