from django.template.loader_tags import IncludeNode
from django.template.loader import get_template


class SnippetsIncludeNode(IncludeNode):
    def get_nodelist(self, context):
        return get_template(self.template_name.resolve(context))

    def __repr__(self):
        return '<SnippetsIncludeNode>'