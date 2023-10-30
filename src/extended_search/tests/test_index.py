import inspect

from wagtail.search import index
from extended_search.index import (
    RenamedFieldMixin,
    SearchField,
    AutocompleteField,
    RelatedFields,
)


class TestIndexedModel:
    def test_has_indexmanager_direct_inner_class(self):
        raise AssertionError()

    def test_check_search_fields(self):
        raise AssertionError()


class TestRenamedFieldMixin:
    def test_model_field_name(self):
        raise AssertionError()

    def test_get_field(self):
        raise AssertionError()

    def test_get_attname(self):
        raise AssertionError()

    def test_get_deinition_model(self):
        raise AssertionError()

    def test_get_value(self):
        raise AssertionError()

    def test_mixin_used(self):
        assert index.SearchField in inspect.getmro(SearchField)
        assert RenamedFieldMixin in inspect.getmro(SearchField)
        assert index.AutocompleteField in inspect.getmro(AutocompleteField)
        assert RenamedFieldMixin in inspect.getmro(AutocompleteField)
        assert index.RelatedFields in inspect.getmro(RelatedFields)
        assert RenamedFieldMixin in inspect.getmro(RelatedFields)
