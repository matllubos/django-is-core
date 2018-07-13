from django.contrib.auth.models import User

from is_core.main import UIRESTModelISCore
from is_core.auth.permissions import IsSuperuser, PermissionsSet

from issue_tracker.models import Issue
from issue_tracker.forms import UserForm

from .resources import NumberOfUserIssuesResource


class IsLoggedUserOrSuperuser(IsSuperuser):

    def has_permission(self, name, request, view, obj=None):
        return (
            super().has_permission(name, request, view, obj) or (
                request.user.is_staff and obj is None or obj == request.user
            )
        )


class UserISCore(UIRESTModelISCore):

    model = User
    form_class = UserForm
    ui_list_fields = ('id', '_obj_name')
    permissions = PermissionsSet(
        create=IsSuperuser(),
        update=IsLoggedUserOrSuperuser(),
        read=IsLoggedUserOrSuperuser(),
        delete=IsSuperuser()
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(pk=request.user.pk)
        return qs

    def get_rest_patterns(self):
        rest_patterns = super().get_rest_patterns()
        rest_patterns['api-user-issue'] = self.default_rest_pattern_class(
            'api-number-issues', self.site_name, r'(?P<pk>[-\w]+)/issue-number/', NumberOfUserIssuesResource, self)
        return rest_patterns


class IssueISCore(UIRESTModelISCore):

    model = Issue
    ui_list_fields = ('id', '_obj_name', 'watched_by_string', 'leader__email', 'leader__last_name')
