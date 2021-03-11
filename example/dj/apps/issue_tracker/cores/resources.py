from is_core.rest.resource import RESTResource, RESTModelCoreMixin, RESTModelResource


class NumberOfUserIssuesResource(RESTModelCoreMixin, RESTResource):

    def _get_pk(self):
        return self.kwargs.get(self.pk_name)

    def get(self):
        user = self._get_obj_or_404()
        return {
            'created': user.created_issues.count(),
            'watching': user.watching_issues.count(),
        }


class UserModelResource(RESTModelResource):

    def watching_issues_count(self, obj):
        return obj.watching_issues.count()
    watching_issues_count.short_description = 'watching count'
