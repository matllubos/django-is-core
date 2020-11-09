from django.db.models.query import QuerySet

from pyston.paginator import OffsetBasedPaginator as OriginOffsetBasedPaginator
from pyston.paginator import OffsetBasedPaginatorWithoutTotal as OriginOffsetBasedPaginatorWithoutTotal
from pyston.paginator import CursorBasedPaginator as OriginCursorBasedPaginator

from is_core.config import settings


class OffsetBasedPaginatorMixin:

    type = 'offset-based-paginator'


class OffsetBasedPaginator(OffsetBasedPaginatorMixin, OriginOffsetBasedPaginator):

    type = 'offset-based-paginator'

    def _get_total(self):
        if self.request._rest_context.get('request_count', False):
            if isinstance(self.qs, QuerySet):
                return self.qs.count()
            else:
                return len(self.qs)
        else:
            return None


class OffsetBasedPaginatorWithoutTotal(OffsetBasedPaginatorMixin, OriginOffsetBasedPaginatorWithoutTotal):

    def _get_total(self):
        return None


class CursorBasedPaginator(OriginCursorBasedPaginator):

    type = 'cursor-based-paginator'
