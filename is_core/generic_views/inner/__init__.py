from django.views.generic.base import ContextMixin
from django.template.loader import render_to_string


class InnerView(ContextMixin):

    template_name = None

    def __init__(self, request, parent_view, parent_instance):
        self.request = request
        self.parent_view = parent_view
        self.parent_instance = parent_instance

    def render(self, context, title):
        template = self.template_name
        context.update(self.get_context_data(title=title))
        return render_to_string(template, context.flatten())

    def is_valid(self):
        return True

    def pre_save_parent(self, parent_obj):
        pass

    def post_save_parent(self, parent_obj):
        pass

    def is_changed(self):
        return False

    def get_has_file_field(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self
