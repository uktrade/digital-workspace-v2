import pytest

from extended_search.fields import (
    AbstractBaseField,
    BaseIndexedField,
    IndexedField,
    RelatedIndexedFields,
)
from extended_search.types import AnalysisType


class TestAbstractBaseField:
    def test_init_params_accepted_defaults_and_all_saved_as_kwargs(self):
        field = AbstractBaseField("foo")
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
        } == field.kwargs
        assert field.name == "foo"
        assert field.model_field_name == field.name
        assert field.boost == 1.0

        field = AbstractBaseField("foo", model_field_name="bar", boost=33.7)
        assert {
            "name": "foo",
            "model_field_name": "bar",
            "boost": 33.7,
        } == field.kwargs
        assert field.name == "foo"
        assert field.model_field_name == "bar"
        assert field.boost == 33.7

        field = AbstractBaseField("foo", test="baz")
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "test": "baz",
        } == field.kwargs
        with pytest.raises(AttributeError):
            assert field.test == "baz"

    def test_get_base_mapping_object_format(self):
        field = AbstractBaseField("foo")
        assert {
            "name": field.name,
            "model_field_name": field.model_field_name,
            "boost": field.boost,
            "parent_model_field": None,
        } == field._get_base_mapping_object()

    def test_get_mapping_uses_get_base_mapping_object(self):
        field = AbstractBaseField("foo")
        assert field.get_mapping() == field._get_base_mapping_object()

    def test_mapping_property_uses_get_mapping_method(self, mocker):
        mock_func = mocker.patch(
            "extended_search.fields.AbstractBaseField.get_mapping",
            return_value={"name": "foo"},
        )
        field = AbstractBaseField("foo")
        mapping = field.mapping
        mock_func.assert_called_once()
        assert mapping == field.get_mapping()


class TestBaseIndexedField:
    def test_init_params_accepted_defaults_and_all_saved_as_kwargs(self):
        field = BaseIndexedField("foo")
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "search": False,
            "autocomplete": False,
            "filter": False,
            "fuzzy": False,
        } == field.kwargs
        assert field.name == "foo"
        assert field.model_field_name == field.name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy

        field = BaseIndexedField(
            "foo", search=True, autocomplete=True, filter=True, fuzzy=True
        )
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "search": True,
            "autocomplete": True,
            "filter": True,
            "fuzzy": True,
        } == field.kwargs
        assert field.search
        assert field.autocomplete
        assert field.filter
        assert field.fuzzy

        field = BaseIndexedField("foo", fuzzy=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert field.fuzzy

    def test_get_search_mapping_object_format(self):
        field = BaseIndexedField("foo")
        assert field._get_search_mapping_object() == {}

        field = BaseIndexedField("foo", search=True)
        assert field._get_search_mapping_object() == {"search": []}

        field = BaseIndexedField("foo", fuzzy=True)
        assert field._get_search_mapping_object() == {
            "search": [
                AnalysisType.TOKENIZED,
            ],
            "fuzzy": [],
        }

    def test_get_autocomplete_mapping_object_format(self):
        field = BaseIndexedField("foo")
        assert field._get_autocomplete_mapping_object() == {}

        field = BaseIndexedField("foo", autocomplete=True)
        assert field._get_autocomplete_mapping_object() == {"autocomplete": []}

    def test_get_filter_mapping_object_format(self):
        field = BaseIndexedField("foo")
        assert field._get_filter_mapping_object() == {}

        field = BaseIndexedField("foo", filter=True)
        assert field._get_filter_mapping_object() == {"filter": []}

    def test_get_mapping_uses_sub_methods(self, mocker):
        mock_func = mocker.patch(
            "extended_search.fields.AbstractBaseField.get_mapping",
            return_value={"name": "bar"},
        )
        mock_search = mocker.patch(
            "extended_search.fields.BaseIndexedField._get_search_mapping_object",
            return_value={"search": "baz"},
        )
        mock_autocomplete = mocker.patch(
            "extended_search.fields.BaseIndexedField._get_autocomplete_mapping_object",
            return_value={"autocomplete": "bam"},
        )
        mock_filter = mocker.patch(
            "extended_search.fields.BaseIndexedField._get_filter_mapping_object",
            return_value={"filter": "foobar"},
        )
        field = BaseIndexedField("foo")
        assert field.get_mapping() == {"name": "bar"}
        mock_func.assert_called_once()
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        field = BaseIndexedField("foo", search=True)
        assert field.get_mapping() == {"name": "bar", "search": "baz"}
        mock_search.assert_called_once()

        field = BaseIndexedField("foo", autocomplete=True)
        assert field.get_mapping() == {"name": "bar", "autocomplete": "bam"}
        mock_autocomplete.assert_called_once()

        field = BaseIndexedField("foo", filter=True)
        assert field.get_mapping() == {"name": "bar", "filter": "foobar"}
        mock_filter.assert_called_once()

        field = BaseIndexedField("foo", search=True, autocomplete=True, filter=True)
        assert field.get_mapping() == {
            "name": "bar",
            "search": "baz",
            "autocomplete": "bam",
            "filter": "foobar",
        }


class TestIndexedField:
    def test_init_params_accepted_defaults_and_all_saved_as_kwargs(self):
        field = IndexedField("foo")
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "search": False,
            "autocomplete": False,
            "filter": False,
            "fuzzy": False,
            "tokenized": False,
            "explicit": False,
            "keyword": False,
            "proximity": False,
        } == field.kwargs
        assert field.name == "foo"
        assert field.model_field_name == field.name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy
        assert not field.tokenized
        assert not field.explicit
        assert not field.keyword
        assert not field.proximity

        field = IndexedField(
            "foo",
            search=True,
            tokenized=True,
            explicit=True,
            keyword=True,
            proximity=True,
        )
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "search": True,
            "autocomplete": False,
            "filter": False,
            "fuzzy": False,
            "tokenized": True,
            "explicit": True,
            "keyword": True,
            "proximity": True,
        } == field.kwargs
        assert field.tokenized
        assert field.explicit
        assert field.keyword
        assert field.proximity

    def test_init_params_set_search_param_when_needed(self):
        field = IndexedField("foo", tokenized=True)
        assert field.search
        assert field.tokenized
        assert not field.explicit
        assert not field.keyword
        assert not field.proximity

        field = IndexedField("foo", explicit=True)
        assert field.search
        assert field.explicit
        assert not field.tokenized
        assert not field.keyword
        assert not field.proximity

        field = IndexedField("foo", keyword=True)
        assert field.search
        assert field.keyword
        assert not field.tokenized
        assert not field.explicit
        assert not field.proximity

        field = IndexedField("foo", proximity=True)
        assert not field.search
        assert field.proximity
        assert not field.tokenized
        assert not field.explicit
        assert not field.keyword

    def test_get_search_mapping_object_format(self):
        field = IndexedField("foo", tokenized=True)
        mapping = field._get_search_mapping_object()
        assert mapping == {"search": [AnalysisType.TOKENIZED]}

        field = IndexedField("foo", explicit=True)
        mapping = field._get_search_mapping_object()
        assert mapping == {"search": [AnalysisType.EXPLICIT]}

        field = IndexedField("foo", keyword=True)
        mapping = field._get_search_mapping_object()
        assert mapping == {"search": [AnalysisType.KEYWORD]}

        field = IndexedField("foo", proximity=True)
        mapping = field._get_search_mapping_object()
        assert mapping == {}

        field = IndexedField(
            "foo", tokenized=True, explicit=True, keyword=True, proximity=True
        )
        mapping = field._get_search_mapping_object()
        assert mapping == {
            "search": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
                AnalysisType.KEYWORD,
                # AnalysisType.PROXIMITY,
            ]
        }

    def test_get_search_mapping_object_uses_parent_method(self, mocker):
        mock_search = mocker.patch(
            "extended_search.fields.BaseIndexedField._get_search_mapping_object",
            return_value={"search": []},
        )
        field = IndexedField("foo")
        field._get_search_mapping_object()
        mock_search.assert_called_once()


class TestRelatedIndexedFields:
    def test_init_params_accepted_defaults_and_all_saved_as_kwargs(self):
        field = RelatedIndexedFields("foo", ["bar", "baz"])
        assert {
            "name": "foo",
            "model_field_name": "foo",
            "boost": 1.0,
            "related_fields": ["bar", "baz"],
        } == field.kwargs
        assert field.name == "foo"
        assert field.model_field_name == field.name
        assert field.boost == 1.0
        assert field.related_fields == ["bar", "baz"]

    def test_get_related_mapping_object_format(self, mocker):
        mock_field = mocker.Mock()
        mock_second_field = mocker.Mock()
        mock_field.get_mapping.return_value = {"field_name": "--FOO--"}
        mock_second_field.get_mapping.return_value = {"field_name": "--BAR--"}
        field = RelatedIndexedFields("foo", [mock_field, mock_second_field])
        mapping = field._get_related_mapping_object()
        assert {
            "related_fields": [
                {
                    "field_name": "--FOO--",
                    "parent_model_field": "foo",
                },
                {
                    "field_name": "--BAR--",
                    "parent_model_field": "foo",
                },
            ]
        } == mapping

    def test_get_mapping_uses_sub_methods(self, mocker):
        mock_func = mocker.patch(
            "extended_search.fields.AbstractBaseField.get_mapping", return_value={}
        )
        mock_related = mocker.patch(
            "extended_search.fields.RelatedIndexedFields._get_related_mapping_object",
            return_value={},
        )
        field = RelatedIndexedFields("foo", ["bar", "baz"])
        field.get_mapping()
        mock_func.assert_called_once()
        mock_related.assert_called_once()
