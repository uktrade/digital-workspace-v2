import pytest
from django.db import models
from wagtail.search import index

from extended_search.index import (
    SearchField,
    RelatedFields,
    AutocompleteField,
    Indexed,
    RenamedFieldMixin,
)


class TestIndexed:
    @pytest.mark.xfail
    def test_check_search_fields_uses_model_field_name(self):
        ...
        # class TestModel(Indexed):
        #     search_fields = [SearchField("foo")]

        # TestModel._meta = mocker.mock()

        # assert TestModel._check_search_fields() == []


class TestRenamedFieldMixin:
    def test_get_field_uses_model_field_name(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model._meta.get_field.return_value = None
        original_field = index.SearchField("foo")
        original_field.get_field(mock_model)
        assert mock_model._meta.get_field.called_with("foo")

        mock_model.reset_mock()
        field = SearchField("foo", model_field_name="bar")
        field.get_field(mock_model)
        assert mock_model._meta.get_field.not_called_with("foo")
        assert mock_model._meta.get_field.called_with("barll")

    @pytest.mark.xfail
    def test_get_field_uses_parent(self):
        ...

    @pytest.mark.xfail
    def test_get_definition_model_uses_model_field_name(self):
        ...

    @pytest.mark.xfail
    def test_get_definition_model_uses_parent(self):
        ...

    @pytest.mark.xfail
    def test_get_value_uses_model_field_name(self):
        ...

    @pytest.mark.xfail
    def test_get_value_uses_parent(self):
        ...


class TestAutocompleteField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(AutocompleteField, RenamedFieldMixin)
        assert issubclass(AutocompleteField, index.AutocompleteField)


class TestSearchField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(SearchField, RenamedFieldMixin)
        assert issubclass(SearchField, index.SearchField)


class TestRelatedFields:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(RelatedFields, RenamedFieldMixin)
        assert issubclass(RelatedFields, index.RelatedFields)
