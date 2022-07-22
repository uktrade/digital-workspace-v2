from django.conf import settings
from rest_framework import pagination


class ApiPagination(pagination.CursorPagination):
    page_size = settings.PAGINATION_PAGE_SIZE
    max_page_size = settings.PAGINATION_MAX_PAGE_SIZE
    page_size_query_param = "page_size"
