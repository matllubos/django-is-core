from chamber.shortcuts import get_object_or_404

from is_core.rest.resource import RESTResource


class NumberOfUserIssuesResource(RESTResource):

    def _get_pk(self):
        return self.kwargs.get(self.pk_name)

    def _get_queryset(self):
        return self.core.get_queryset(self.request)

    def _get_obj_or_404(self, pk=None):
        return get_object_or_404(self._get_queryset(), pk=(pk or self._get_pk()))

    def get(self):
        user = self._get_obj_or_404()
        return {
            'created': user.created_issues.count(),
            'watching': user.watching_issues.count(),
        }
