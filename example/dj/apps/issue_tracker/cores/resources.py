from is_core.rest.resource import RESTResource, RESTModelCoreMixin


class NumberOfUserIssuesResource(RESTModelCoreMixin, RESTResource):

    def get(self):
        user = self._get_obj_or_404()
        return {
            'created': user.created_issues.count(),
            'watching': user.watching_issues.count(),
        }
