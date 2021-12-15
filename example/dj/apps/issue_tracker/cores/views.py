from is_core.generic_views.detail_views import DjangoDetailFormView


class UserDetailView(DjangoDetailFormView):

    def leading_issue_name(self, obj):
        return obj.leading_issue.name if hasattr(obj, 'leading_issue') else 'No leading issue'
    leading_issue_name.short_description = 'leading issue name'
