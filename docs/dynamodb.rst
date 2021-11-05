.. _dynamodb:

DynamoDB
========

Library has support for DynamoDB database. For this purpose you must have installed ``pydjamodb`` library. Next you can use special core base class to implement DynamoDB REST endpoint. Implementation is little bit complicated because you must implement custom UI and REST patterns because DynamoDB objects ID consists of two fields::

    from pydjamodb.models import DynamoModel
    from pynamodb.attributes import (
        MapAttribute, NumberAttribute, UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, NumberAttribute
    )

    class Comment(DynamoModel):

        issue_id = UnicodeAttribute(hash_key=True)
        user_id = UnicodeAttribute(range_key=True)
        content = UnicodeAttribute()
        is_public = BooleanAttribute()
        priority = NumberAttribute()

        class Meta:
            table_name = 'comment'


    from django.shortcuts import resolve_url

    from is_core.contrib.dynamo.cores import DynamoUiRestCore
    from is_core.patterns import RestPattern, UiPattern, PK_PATTERN


    class CommentPatternMixin:

        def _get_try_kwargs(self, request, obj):
            if obj and PK_PATTERN in self.url_pattern:
                return {
                    'issue_pk': obj.issue_id if obj else 0,
                    'pk': obj.user_id if obj else None
                }
            else:
                return {'issue_pk': obj.issue_id if obj else 0}


    class CommentRestPattern(CommentPatternMixin, RestPattern):
        pass


    class CommentUiPattern(CommentPatternMixin, UiPattern):
        pass


    class DynamoCommentCore(DynamoUiRestCore):

        model = Comment
        menu_group = 'dynamodb-comment'

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
            return '/'.join(list(self.get_menu_groups()) + ['(?P<issue_pk>[^/]+)'])  # added hash key value to URL


Due database restrictions resource ordering can be performed only via range key. Filters must be added by hand. Pagination is performed via cursor based paginator.

Right now ``DynamoUiRestCore`` support only reading from the database.
