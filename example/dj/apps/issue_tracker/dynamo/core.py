from django.shortcuts import resolve_url

from is_core.contrib.dynamo.cores import DynamoUiRestCore
from is_core.patterns import RestPattern, UiPattern, PK_PATTERN

from .models import Comment


class CommentPatternMixin:

    def _get_try_kwargs(self, request, obj):
        if obj and PK_PATTERN in self.url_pattern:
            return {
                'issue_pk': obj.issue_id,
                'pk': obj.user_id
            }
        else:
            return {'issue_pk': obj.issue_id if obj else 0}


class CommentRestPattern(CommentPatternMixin, RestPattern):
    pass


class CommentUiPattern(CommentPatternMixin, UiPattern):
    pass


class DynamoCommentCore(DynamoUiRestCore):

    model = Comment
    menu_group = 'dynamo-comment'

    fields = ('user_id', 'content', 'is_public', 'priority')

    verbose_name = 'comment'
    verbose_name_plural = 'comments'

    default_rest_pattern_class = CommentRestPattern
    default_ui_pattern_class = CommentUiPattern

    rest_range_key = 'user_id'

    def _get_hash_key(self, request):
        return request.kwargs.get('issue_pk')

    def get_api_url(self, request):
        return resolve_url(self.get_api_url_name(), issue_pk=self._get_hash_key(request))

    def get_url_prefix(self):
        return '/'.join(list(self.get_menu_groups()) + ['(?P<issue_pk>[^/]+)'])
