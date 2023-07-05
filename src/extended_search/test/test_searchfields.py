import pytest

from extended_search.index import (
    SearchField,
    RelatedFields,
    AutocompleteField,
    Indexed,
    RenamedFieldMixin,
)


pytestmark = pytest.mark.xfail


class TestIndexed:
    def test_check_search_fields_uses_model_field_name(self):
        ...


class TestRenamedFieldMixin:
    def test_get_field_uses_model_field_name(self):
        ...

    def test_get_field_uses_parent(self):
        ...

    def test_get_definition_model_uses_model_field_name(self):
        ...

    def test_get_definition_model_uses_parent(self):
        ...

    def test_get_value_uses_model_field_name(self):
        ...

    def test_get_value_uses_parent(self):
        ...


class TestAutocompleteField:
    def test_extends_renamedfieldmixin(self):
        ...


class TestSearchField:
    def test_extends_renamedfieldmixin(self):
        ...


class TestRelatedFields:
    def test_extends_renamedfieldmixin(self):
        ...
