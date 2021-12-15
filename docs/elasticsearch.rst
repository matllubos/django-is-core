.. _elasticsearch:

Elasticsearch
=============

Library has support for elasticsearch database. For this purpose you must have installed ``elasticsearch`` and ``elasticsearch-dsl`` libraries. Next you can use special base core class to implement elasticsearch administration::

    from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, Boolean

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


    from is_core.contrib.elasticsearch.cores import ElasticsearchURestCore

    class ElasticsearchCommentCore(ElasticsearchURestCore):

        model = Comment
        menu_group = 'elasticsearch-comment'

        fields = ('id', 'user_id', 'content', 'is_public', 'priority')

        verbose_name = 'comment'
        verbose_name_plural = 'comments'


Filtering, ordering and pagination is automatically added to the resource with the same was as ``DjangoModelUIRESTISCore``.

Right now ``ElasticsearchURestCore`` support only reading from the database.
