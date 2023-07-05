import pytest

from extended_search.backends.backend import (
    ExtendedSearchQueryCompiler,
    OnlyFieldSearchQueryCompiler,
    CustomSearchBackend,
)


pytestmark = pytest.mark.xfail


class TestExtendedSearchQueryCompiler:
    def test_remap_fields_works_the_same_as_parent_init(self):
        ...

    def test_join_compile_queries_output_format(self):
        ...

    def test_join_compile_queries_uses_compile_query(self):
        ...

    def test_get_inner_query_works_the_same_as_parent(self):
        ...


class TestOnlyFieldSearchQueryCompiler:
    def test_compile_query_uses_parent_when_not_onlyfields(self):
        ...

    def test_compile_query_uses_remap_fields(self):
        ...

    def test_compile_query_onlyfields_logic(self):
        ...

    def test_compile_query_match_none_uses_wagtail_const(self):
        ...


class TestCustomSearchBackend:
    def test_correct_mappings_and_backends_configured(self):
        ...

    def test_custom_search_backend_used(self):
        ...
