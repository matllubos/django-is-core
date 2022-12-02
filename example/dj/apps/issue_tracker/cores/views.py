from is_core.generic_views.detail_views import DjangoDetailFormView
from is_core.generic_views.inlines.inline_form_views import TabularInlineFormView

from issue_tracker.models import Issue


class UserDetailView(DjangoDetailFormView):

    def leading_issue_name(self, obj):
        return obj.leading_issue.name if hasattr(obj, 'leading_issue') else 'No leading issue'
    leading_issue_name.short_description = 'leading issue name'


class SubIssuesView(TabularInlineFormView):

    model = Issue
