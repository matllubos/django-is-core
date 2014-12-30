from django.views.generic.base import TemplateView

from is_core.generic_views import DefaultViewMixin
from is_core.patterns import patterns, RestPattern


class RestDocumentationView(DefaultViewMixin, TemplateView):
    template_name = 'generic_views/rest_documentation.html'

    def get_context_data(self, **kwargs):
        context_data = super(RestDocumentationView, self).get_context_data(**kwargs)
        rest_patterns = {}
        for pattern_name, pattern in patterns.items():
            if isinstance(pattern, RestPattern):
                rest_patterns[pattern_name] = pattern
        context_data['pattern_list'] = rest_patterns
        return context_data

