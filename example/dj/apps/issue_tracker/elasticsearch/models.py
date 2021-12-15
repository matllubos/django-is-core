from django.conf import settings

from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, Boolean
from elasticsearch_dsl import connections


connections.create_connection(**settings.ELASTICSEARCH_DATABASE)


class Comment(Document):

    user_id = Keyword()
    content = Text()
    is_public = Boolean()
    priority = Integer()

    @property
    def id(self):
        return self.meta.id

    @property
    def pk(self):
        return self.meta.id

    def __str__(self):
        return self.id

    class Index:
        name = 'comment'


Comment.init()
