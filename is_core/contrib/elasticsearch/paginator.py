from pyston.contrib.elasticsearch.paginator import \
    ElasticsearchOffsetBasedPaginator as OriginElasticsearchOffsetBasedPaginator


class ElasticsearchOffsetBasedPaginator(OriginElasticsearchOffsetBasedPaginator):

    type = 'offset-based-paginator'

    def _get_total(self, qs, request):
        if request._rest_context.get('request_count', False):
            return super()._get_total(qs, request)
        else:
            return None
