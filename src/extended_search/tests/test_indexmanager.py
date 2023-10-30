import pytest

from wagtail.search.index import FilterField
from extended_search.index import AutocompleteField, SearchField, RelatedFields
from extended_search.managers.index import ModelIndexManager
from extended_search.managers.query_builder import QueryBuilder
from extended_search.models import Setting
from extended_search.types import AnalysisType


class TestModelIndexManager:
    def test_extends_querybuilder(self):
        assert issubclass(ModelIndexManager, QueryBuilder)

    def test_new_returns_get_search_fields(self, mocker):
        mock_func = mocker.patch(
            "extended_search.managers.index.ModelIndexManager.get_search_fields",
        )
        ModelIndexManager()
        mock_func.assert_called_once()

    def test_get_search_fields_uses_mapping_and_submethod(self, mocker):
        mock_mapping = mocker.patch(
            "extended_search.managers.index.ModelIndexManager.get_mapping",
            return_value=["foo"],
        )
        mock_submethod = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_search_fields_from_mapping"
        )
        ModelIndexManager.get_search_fields()
        mock_mapping.assert_called_once()
        mock_submethod.assert_called_once_with("foo")

    def test_get_search_fields_returns_all_fields(self, mocker):
        mock_mapping = mocker.patch(
            "extended_search.managers.index.ModelIndexManager.get_mapping",
            return_value=["foo"],
        )
        mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_search_fields_from_mapping",
            return_value=[
                "bam",
            ],
        )
        assert len(ModelIndexManager.get_search_fields()) == 1

        mock_mapping.return_value = ["foo", "bar", "baz"]
        assert len(ModelIndexManager.get_search_fields()) == 3

    def test_get_mapping_returns_field_mappings(self, mocker):
        mock_field = mocker.Mock()
        mock_field.mapping = "--MAP--"
        ModelIndexManager.fields = [mock_field]
        assert ModelIndexManager.get_mapping() == ["--MAP--"]

        ModelIndexManager.fields = [
            mock_field,
            mock_field,
            mock_field,
        ]
        assert ModelIndexManager.get_mapping() == ["--MAP--", "--MAP--", "--MAP--"]

    def test_get_search_fields_from_mapping_uses_relevant_submethods(self, mocker):
        mock_related = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_related_fields",
            return_value=["RELATED"],
        )
        mock_search = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_searchable_search_fields",
            return_value=["SEARCH"],
        )
        mock_autocomplete = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_autocomplete_search_fields",
            return_value=["AC"],
        )
        mock_filter = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_filterable_search_fields",
            return_value=["FILTER"],
        )

        mapping = {"model_field_name": "foo"}
        assert [] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mapping = {"model_field_name": "foo", "related_fields": "--ANYTHING--"}
        assert ["RELATED"] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_called_once_with("foo", "--ANYTHING--")
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mock_related.reset_mock()
        mapping = {"model_field_name": "foo", "search": "--SOMETHING--", "boost": 12.9}
        assert ["SEARCH"] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_called_once_with("foo", "--SOMETHING--", 12.9)
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mock_search.reset_mock()
        mapping = {"model_field_name": "foo", "autocomplete": "--NOTHING--"}
        assert ["AC"] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_not_called()
        mock_autocomplete.assert_called_once_with("foo")
        mock_filter.assert_not_called()

        mock_autocomplete.reset_mock()
        mapping = {"model_field_name": "foo", "filter": "--EVERYTHING--"}
        assert ["FILTER"] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_called_once_with("foo")

        mock_filter.reset_mock()
        mapping = {
            "model_field_name": "foo",
            "related_fields": "--EVERYTHING--",
            "search": "--NOTHING--",
            "autocomplete": "--SOMETHING--",
            "filter": "--ANYTHING--",
            "boost": 22.5,
        }
        assert [
            "RELATED",
            "SEARCH",
            "AC",
            "FILTER",
        ] == ModelIndexManager._get_search_fields_from_mapping(mapping)
        mock_related.assert_called_once_with("foo", "--EVERYTHING--")
        mock_search.assert_called_once_with("foo", "--NOTHING--", 22.5)
        mock_autocomplete.assert_called_once_with("foo")
        mock_filter.assert_called_once_with("foo")

    def test_get_autocomplete_search_fields_returns_extended_autocompletefield(self):
        result = ModelIndexManager._get_autocomplete_search_fields("foo")
        assert type(result) == list
        assert type(result[0]) == AutocompleteField
        assert result[0].field_name == "foo"

    def test_get_filterable_search_fields_returns_wagtail_filterfield(self):
        result = ModelIndexManager._get_filterable_search_fields("foo")
        assert type(result) == list
        assert type(result[0]) == FilterField
        assert result[0].field_name == "foo"

    def test_get_searchable_search_fields_returns_extended_searchfields(self, mocker):
        mock_fieldname = mocker.patch(
            "extended_search.managers.index.get_indexed_field_name",
            return_value="bar",
        )
        mock_analyzer = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_analyzer_name",
            return_value="baz",
        )
        result = ModelIndexManager._get_searchable_search_fields("foo", [], 3.2)
        assert len(result) == 1
        assert type(result[0]) == SearchField
        assert result[0].field_name == "bar"
        assert result[0].boost == 3.2
        assert result[0].kwargs["model_field_name"] == "foo"
        assert result[0].kwargs["es_extra"] == {"analyzer": "baz"}
        # uses help methods
        mock_fieldname.assert_called_once_with(
            "foo",
            AnalysisType.TOKENIZED,
        )
        # analyzer defaults to tokenized
        mock_analyzer.assert_called_once_with(AnalysisType.TOKENIZED)

    def test_get_searchable_search_fields_returns_field_per_analyzer(self, mocker):
        mocker.patch(
            "extended_search.managers.index.get_indexed_field_name",
            return_value="bar",
        )
        mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_analyzer_name",
            return_value="baz",
        )
        assert (
            len(ModelIndexManager._get_searchable_search_fields("foo", [], boost=22.5))
            == 1
        )
        assert (
            len(ModelIndexManager._get_searchable_search_fields("foo", ["first"])) == 1
        )
        assert (
            len(
                ModelIndexManager._get_searchable_search_fields(
                    "foo", ["first", "second"]
                )
            )
            == 2
        )
        assert (
            len(
                ModelIndexManager._get_searchable_search_fields(
                    "foo", ["first", "second", "three"]
                )
            )
            == 3
        )

    def test_get_related_fields_returns_extended_relatedfields(self, mocker):
        mock_func = mocker.patch(
            "extended_search.managers.index.ModelIndexManager._get_search_fields_from_mapping",
            return_value=["SearchFieldObject <bar>"],
        )
        result = ModelIndexManager._get_related_fields("foo", [{"field_name": "baz"}])
        mock_func.assert_called_once_with({"field_name": "baz"})
        assert type(result) == list
        assert type(result[0]) == RelatedFields
        assert result[0].field_name == "foo"
        assert result[0].fields == ["SearchFieldObject <bar>"]

        mock_func.reset_mock()
        result = ModelIndexManager._get_related_fields(
            "foo",
            [{"field_name": "baz"}, {"field_name": "bam"}, {"field_name": "foobar"}],
        )
        assert mock_func.call_count == 3
        assert len(result[0].fields) == 3

    @pytest.mark.django_db
    def test_get_analyzer_name_retrieves_value_from_settings(self):
        Setting.objects.create(key="analyzers__tokenized__es_analyzer", value="foo")
        assert AnalysisType.TOKENIZED.value == "tokenized"
        assert ModelIndexManager._get_analyzer_name(AnalysisType.TOKENIZED) == "foo"
        Setting.objects.create(key="analyzers__explicit__es_analyzer", value="bar")
        assert AnalysisType.EXPLICIT.value == "explicit"
        assert ModelIndexManager._get_analyzer_name(AnalysisType.EXPLICIT) == "bar"

    def test_get_directly_defined_fields(self):
        raise AssertionError()

    def test_is_directly_defined(self):
        raise AssertionError()
