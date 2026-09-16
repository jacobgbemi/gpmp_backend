"""Standard pagination for GlintPM Private APIs."""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Default pagination used across the API.

    Clients may override the page size with `?page_size=`, capped at 100
    to protect the database and network from oversized responses.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
