import pytest

from extended_search.managers.index import ModelIndexManager


pytestmark = pytest.mark.xfail


class TestModelIndexManager:
    def test_extends_querybuilder(self):
        ...

    def test_new_returns_get_search_fields(self):
        ...

    def test_get_search_fields_uses_mapping_and_submethod(self):
        ...

    def test_get_search_fields_returns_all_fields(self):
        ...

    def test_get_mapping_returns_field_mappings(self):
        ...

    def test_get_search_fields_from_mapping_uses_relevant_submethods(self):
        ...

    def test_get_autocomplete_search_fields_returns_extended_autocompletefield(self):
        ...

    def test_get_filterable_search_fields_returns_wagtail_filterfield(self):
        ...

    def test_get_searchable_search_fields_returns_extended_searchfields(self):
        ...

    def test_get_searchable_search_fields_defaults_to_tokenized(self):
        ...

    def test_get_searchable_search_fields_uses_get_indexed_field_name(self):
        ...

    def test_get_searchable_search_fields_uses_get_analyzer_name(self):
        ...

    def test_get_searchable_search_fields_returns_field_per_analyzer(self):
        ...

    def test_get_related_fields_returns_extended_relatedfields(self):
        ...

    def test_get_related_fields_uses_get_search_fields_from_mapping(self):
        ...

    def test_get_related_fields_returns_field_per_relatedfield_entry(self):
        ...

    def test_get_analyzer_name_retrieves_value_from_settings(self):
        ...
