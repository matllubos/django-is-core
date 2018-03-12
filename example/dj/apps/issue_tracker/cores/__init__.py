from django.contrib.auth.models import User

from is_core.main import UIRESTModelISCore

from issue_tracker.models import Issue
from issue_tracker.forms import UserForm

from .resources import NumberOfUserIssuesResource


class UserIsCore(UIRESTModelISCore):
    model = User
    form_class = UserForm
    ui_list_fields = ('id', '_obj_name')

    def has_read_permission(self, request, obj=None):
        return request.user.is_superuser or not obj or obj.pk == request.user.pk

    def has_create_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_update_permission(self, request, obj=None):
        return (obj and obj.pk == request.user.pk) or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super(UserIsCore, self).get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(pk=request.user.pk)
        return qs

    def get_rest_patterns(self):
        rest_patterns = super(UserIsCore, self).get_rest_patterns()
        rest_patterns['api-user-issue'] = self.default_rest_pattern_class(
            'api-number-issues', self.site_name, r'(?P<pk>[-\w]+)/issue-number/', NumberOfUserIssuesResource, self)
        return rest_patterns


class IssueIsCore(UIRESTModelISCore):
    model = Issue
    ui_list_fields = ('id', '_obj_name', 'watched_by_string', 'leader__email', 'leader__last_name')

    def has_rest_create_permission(self, request, obj=None, via=None):
        return bool(via) and via[0].model == User
