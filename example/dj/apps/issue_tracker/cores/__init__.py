from django.contrib.auth.models import User

from is_core.main import UIRESTModelISCore
from is_core.generic_views.inlines.inline_form_views import TabularInlineFormView

from issue_tracker.models import Issue
from issue_tracker.forms import UserForm

from .resources import NumberOfUserIssuesResource


class ReportedIssuesInlineView(TabularInlineFormView):
    model = Issue
    fk_name = 'created_by'


class UserIsCore(UIRESTModelISCore):
    model = User
    form_class = UserForm
    form_inline_views = [ReportedIssuesInlineView]
    list_display = ('id', '_obj_name')

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

    def get_resource_patterns(self):
        resource_patterns = super(UserIsCore, self).get_resource_patterns()
        resource_patterns['api-user-issue'] = self.rest_resource_pattern_class(
            'api-number-issues', self.site_name, r'^/(?P<pk>[-\w]+)/issue-number/?$', NumberOfUserIssuesResource, self)
        return resource_patterns


class IssueIsCore(UIRESTModelISCore):
    model = Issue
    list_display = ('id', '_obj_name', 'watched_by_string', 'leader__email', 'leader__last_name')

    def has_rest_create_permission(self, request, obj=None, via=None):
        return bool(via) and via[0].model == User
