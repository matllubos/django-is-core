from django.contrib.auth.models import User

from chamber.shortcuts import get_object_or_404

from is_core.rest.resource import CoreResource, DjangoCoreResource


class NumberOfUserIssuesResource(CoreResource,):

    def get(self):
        user = get_object_or_404(self.core.get_queryset(self.request), pk=self.kwargs.get('pk'))
        return {
            'created': user.created_issues.count(),
            'watching': user.watching_issues.count(),
        }


class UserModelResource(DjangoCoreResource):

    def watching_issues_count(self, obj):
        return obj.watching_issues.count()
    watching_issues_count.short_description = 'watching count'
