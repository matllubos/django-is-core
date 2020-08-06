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
        if isinstance(self.qs, QuerySet):
            if self.qs[:settings.REST_PAGINATOR_MAX_TOTAL+1].count() > settings.REST_PAGINATOR_MAX_TOTAL:
                return None
            else:
                return self.qs.count()
        else:
            return len(self.qs)


class OffsetBasedPaginatorWithoutTotal(OffsetBasedPaginatorMixin, OriginOffsetBasedPaginatorWithoutTotal):

    def _get_total(self):
        return None


class CursorBasedPaginator(OriginCursorBasedPaginator):

    type = 'cursor-based-paginator'
