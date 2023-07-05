import pytest

from extended_search.managers.query_builder import QueryBuilder


pytestmark = pytest.mark.xfail


class TestQueryBuilder:
    def test_get_indexed_field_name_uses_settings_correctly(self):
        ...

    def test_get_inner_searchquery_for_querytype_doesnt_use_and_if_single_word(self):
        # test uses split_query?
        ...

    def test_get_inner_searchquery_for_querytype_handles_searchquerytypes(self):
        ...

    def test_get_boost_for_field_querytype_analysistype_handles_searchquerytypes(self):
        ...

    def test_get_boost_for_field_querytype_analysistype_handles_analysistypes(self):
        ...

    def test_get_boost_for_field_querytype_analysistype_uses_all_3_boosts(self):
        ...

    def test_get_searchquery_for_etc_uses_submethods(self):
        ...

    def test_get_searchquery_for_etc_returns_none_for_none_query_from_submethod(self):
        ...

    def test_get_searchquery_for_etc_output_structure(self):
        ...

    def test_add_to_query(self):
        ...

    def test_get_search_query_from_mapping_uses_settings_and_submethods(self):
        ...

    def test_get_search_query_from_mapping_gets_right_number_of_subqueries(self):
        ...

    def test_get_search_query_from_mapping_handles_relatedfields(self):
        ...

    def test_get_search_query_from_mapping_handles_searchfield(self):
        ...

    def test_get_search_query_from_mapping_handles_filterfield(self):
        ...

    def test_get_search_query_from_mapping_handles_autocompletefield(self):
        ...

    def test_get_search_query_uses_mapping(self):
        ...

    def test_get_search_query_returns_right_set_of_fields(self):
        ...
