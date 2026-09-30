from rest_framework.pagination import CursorPagination


class NamePagination(CursorPagination):
    ordering = 'name'


class NameIdPagination(CursorPagination):
    ordering = ('name', 'id')


class PublishedPagination(CursorPagination):
    ordering = '-published'
    page_size = 20
    page_size_query_param = 'page_size'


class SortOrderPagination(CursorPagination):
    ordering = 'sort_order'
