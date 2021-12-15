from is_core.contrib.elasticsearch.cores import ElasticsearchUiRestCore

from .models import Comment


class ElasticsearchCommentCore(ElasticsearchUiRestCore):

    model = Comment
    menu_group = 'elasticsearch-comment'

    fields = ('id', 'user_id', 'content', 'is_public', 'priority')

    verbose_name = 'comment'
    verbose_name_plural = 'comments'
