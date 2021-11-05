from pyston.contrib.dynamo.paginator import DynamoCursorBasedPaginator as OriginDynamoCursorBasedPaginator


class DynamoCursorBasedPaginator(OriginDynamoCursorBasedPaginator):

    type = 'cursor-based-paginator'
