from django.db.models.query import QuerySet

from pyston.paginator import OffsetBasedPaginator as OriginOffsetBasedPaginator
from pyston.paginator import OffsetBasedPaginatorWithoutTotal as OriginOffsetBasedPaginatorWithoutTotal
from pyston.paginator import CursorBasedPaginator as OriginCursorBasedPaginator

from is_core.config import settings


class OffsetBasedPaginatorMixin:

    type = 'offset-based-paginator'


class OffsetBasedPaginator(OffsetBasedPaginatorMixin, OriginOffsetBasedPaginator):

    type = 'offset-based-paginator'

    def _get_total(self, qs, request):
        if request._rest_context.get('request_count', False):
            return super()._get_total(qs, request)
        else:
            return None


class CursorBasedPaginator(OriginCursorBasedPaginator):

    type = 'cursor-based-paginator'
