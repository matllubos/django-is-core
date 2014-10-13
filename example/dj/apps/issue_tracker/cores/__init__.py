from django.contrib.auth.models import User

from is_core.main import UIRestModelISCore

from issue_tracker.models import Issue
from issue_tracker.forms import UserForm



class UserIsCore(UIRestModelISCore):
    model = User
    form_class = UserForm

    def has_read_permission(self, request, obj=None):
        return (obj and obj.pk == request.user.pk) or request.user.is_superuser

    def has_create_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_update_permission(self, request, obj=None):
        return (obj and obj.pk == request.user.pk) or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class IssueIsCore(UIRestModelISCore):
    model = Issue
