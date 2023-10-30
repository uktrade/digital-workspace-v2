import inspect
import pytest

from wagtail.search import index
from extended_search.managers import (
    get_indexed_field_name,
    get_query_for_model,
    get_search_query,
)

class TestManagersInit:
    def test_get_indexed_field_name(self):
        assert False

    def test_get_query_for_model(self):
        assert False

    def test_get_search_query(self, mocker):
        assert False
