from pyston.paginator import DjangoOffsetBasedPaginator as OriginDjangoOffsetBasedPaginator
from pyston.paginator import DjangoCursorBasedPaginator as OriginDjangoCursorBasedPaginator


class DjangoOffsetBasedPaginator(OriginDjangoOffsetBasedPaginator):

    type = 'offset-based-paginator'

    def _get_total(self, qs, request):
        if request._rest_context.get('request_count', False):
            return super()._get_total(qs, request)
        else:
            return None


class DjangoCursorBasedPaginator(OriginDjangoCursorBasedPaginator):

    type = 'cursor-based-paginator'
