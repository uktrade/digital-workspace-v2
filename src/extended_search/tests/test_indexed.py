import pytest
from extended_search.index import AutocompleteField, Indexed, RelatedFields, SearchField
from extended_search.models import Setting
from extended_search.types import AnalysisType
from wagtail.search.index import FilterField


class TestIndexed:
    @pytest.mark.xfail
    def test_get_indexed_fields_uses_submethod(self, mocker):
        mock_submethod = mocker.patch(
            "extended_search.index.Indexed._get_indexed_fields_from_mapping"
        )
        Indexed.get_indexed_fields()
        mock_submethod.assert_called_once_with("foo")

    @pytest.mark.xfail
    def test_get_indexed_fields_returns_all_fields(self, mocker):
        mock_mapping = mocker.patch(
            "extended_search.index.Indexed.get_mapping",
            return_value=["foo"],
        )
        mocker.patch(
            "extended_search.index.Indexed._get_indexed_fields_from_mapping",
            return_value=[
                "bam",
            ],
        )
        assert len(Indexed.get_indexed_fields()) == 1

        mock_mapping.return_value = ["foo", "bar", "baz"]
        assert len(Indexed.get_indexed_fields()) == 3

    @pytest.mark.xfail
    def test_get_indexed_fields_from_mapping_uses_relevant_submethods(self, mocker):
        mock_related = mocker.patch(
            "extended_search.index.Indexed._get_related_fields",
            return_value=["RELATED"],
        )
        mock_search = mocker.patch(
            "extended_search.index.Indexed._get_searchable_search_fields",
            return_value=["SEARCH"],
        )
        mock_autocomplete = mocker.patch(
            "extended_search.index.Indexed._get_autocomplete_search_fields",
            return_value=["AC"],
        )
        mock_filter = mocker.patch(
            "extended_search.index.Indexed._get_filterable_search_fields",
            return_value=["FILTER"],
        )

        mapping = {"model_field_name": "foo"}
        assert [] == Indexed._get_indexed_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mapping = {"model_field_name": "foo", "related_fields": "--ANYTHING--"}
        assert ["RELATED"] == Indexed._get_indexed_fields_from_mapping(mapping)
        mock_related.assert_called_once_with("foo", "--ANYTHING--")
        mock_search.assert_not_called()
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mock_related.reset_mock()
        mapping = {"model_field_name": "foo", "search": "--SOMETHING--", "boost": 12.9}
        assert ["SEARCH"] == Indexed._get_indexed_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_called_once_with("foo", "--SOMETHING--", 12.9)
        mock_autocomplete.assert_not_called()
        mock_filter.assert_not_called()

        mock_search.reset_mock()
        mapping = {"model_field_name": "foo", "autocomplete": "--NOTHING--"}
        assert ["AC"] == Indexed._get_indexed_fields_from_mapping(mapping)
        mock_related.assert_not_called()
        mock_search.assert_not_called()
        mock_autocomplete.assert_called_once_with("foo")
        mock_filter.assert_not_called()

        mock_autocomplete.reset_mock()
        mapping = {"model_field_name": "foo", "filter": "--EVERYTHING--"}
        assert ["FILTER"] == Indexed._get_indexed_fields_from_mapping(mapping)
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
        ] == Indexed._get_indexed_fields_from_mapping(mapping)
        mock_related.assert_called_once_with("foo", "--EVERYTHING--")
        mock_search.assert_called_once_with("foo", "--NOTHING--", 22.5)
        mock_autocomplete.assert_called_once_with("foo")
        mock_filter.assert_called_once_with("foo")

    @pytest.mark.xfail
    def test_get_autocomplete_search_fields_returns_extended_autocompletefield(self):
        result = Indexed._get_autocomplete_search_fields("foo")
        assert type(result) == list
        assert type(result[0]) == AutocompleteField
        assert result[0].field_name == "foo"

    @pytest.mark.xfail
    def test_get_filterable_search_fields_returns_wagtail_filterfield(self):
        result = Indexed._get_filterable_search_fields("foo")
        assert type(result) == list
        assert type(result[0]) == FilterField
        assert result[0].field_name == "foo"

    @pytest.mark.xfail
    def test_get_searchable_search_fields_returns_extended_searchfields(self, mocker):
        mock_fieldname = mocker.patch(
            "extended_search.managers.index.get_indexed_field_name",
            return_value="bar",
        )
        mock_analyzer = mocker.patch(
            "extended_search.index.Indexed._get_analyzer_name",
            return_value="baz",
        )
        result = Indexed._get_searchable_search_fields("foo", [], 3.2)
        # uses help methods
        mock_fieldname.assert_called_once_with(
            "foo",
            AnalysisType.TOKENIZED,
        )
        # analyzer defaults to tokenized
        mock_analyzer.assert_called_once_with(AnalysisType.TOKENIZED)
        assert len(result) == 1
        assert type(result[0]) == SearchField
        assert result[0].field_name == "bar"
        assert result[0].boost == 3.2
        assert result[0].model_field_name == "foo"
        assert result[0].kwargs["es_extra"] == {"analyzer": "baz"}

    @pytest.mark.xfail
    def test_get_searchable_search_fields_returns_field_per_analyzer(self, mocker):
        mocker.patch(
            "extended_search.managers.index.get_indexed_field_name",
            return_value="bar",
        )
        mocker.patch(
            "extended_search.index.Indexed._get_analyzer_name",
            return_value="baz",
        )
        assert len(Indexed._get_searchable_search_fields("foo", [], boost=22.5)) == 1
        assert len(Indexed._get_searchable_search_fields("foo", ["first"])) == 1
        assert (
            len(Indexed._get_searchable_search_fields("foo", ["first", "second"])) == 2
        )
        assert (
            len(
                Indexed._get_searchable_search_fields(
                    "foo", ["first", "second", "three"]
                )
            )
            == 3
        )

    @pytest.mark.xfail
    def test_get_related_fields_returns_extended_relatedfields(self, mocker):
        mock_func = mocker.patch(
            "extended_search.index.Indexed._get_indexed_fields_from_mapping",
            return_value=["SearchFieldObject <bar>"],
        )
        result = Indexed._get_related_fields("foo", [{"field_name": "baz"}])
        mock_func.assert_called_once_with({"field_name": "baz"})
        assert type(result) == list
        assert type(result[0]) == RelatedFields
        assert result[0].field_name == "foo"
        assert result[0].fields == ["SearchFieldObject <bar>"]

        mock_func.reset_mock()
        result = Indexed._get_related_fields(
            "foo",
            [{"field_name": "baz"}, {"field_name": "bam"}, {"field_name": "foobar"}],
        )
        assert mock_func.call_count == 3
        assert len(result[0].fields) == 3

    @pytest.mark.django_db
    def test_get_analyzer_name_retrieves_value_from_settings(self):
        Setting.objects.create(key="analyzers__tokenized__es_analyzer", value="foo")
        assert AnalysisType.TOKENIZED.value == "tokenized"
        assert Indexed._get_analyzer_name(AnalysisType.TOKENIZED) == "foo"
        Setting.objects.create(key="analyzers__explicit__es_analyzer", value="bar")
        assert AnalysisType.EXPLICIT.value == "explicit"
        assert Indexed._get_analyzer_name(AnalysisType.EXPLICIT) == "bar"

    def test_get_directly_defined_fields(self, mocker):
        class Field:
            field_name = None
            model_field_name = None

        def side_effect():
            Indexed.generated_fields = ["bar"]

        mock_get_indexed_fields = mocker.patch(
            "extended_search.index.Indexed.get_indexed_fields",
            side_effect=side_effect,
        )

        Indexed.indexed_fields = []
        Indexed.generated_fields = None
        Indexed.get_directly_defined_fields()
        mock_get_indexed_fields.assert_called_once()

        mock_get_indexed_fields.reset_mock()
        Indexed.generated_fields = []
        Indexed.get_directly_defined_fields()
        mock_get_indexed_fields.assert_called_once()

        mock_get_indexed_fields.reset_mock()
        Indexed.generated_fields = ["bar"]
        Indexed.get_directly_defined_fields()
        mock_get_indexed_fields.assert_not_called()

        mock_get_indexed_fields.reset_mock()
        fie = Field()
        fie.model_field_name = "foo"
        gen = Field()
        gen.field_name = "bar"
        Indexed.indexed_fields = [fie]
        Indexed.generated_fields = [gen]
        assert Indexed.get_directly_defined_fields() == []

        gen.field_name = "foo"
        assert Indexed.get_directly_defined_fields() == []

        gen.model_field_name = "foo"
        assert Indexed.get_directly_defined_fields() == [gen]

        gen2 = Field()
        gen2.model_field_name = "foo"
        Indexed.generated_fields = [gen, gen2]
        assert Indexed.get_directly_defined_fields() == [gen, gen2]

    def test_is_directly_defined(self, mocker):
        mock_get_directly_defined_fields = mocker.patch(
            "extended_search.index.Indexed.get_directly_defined_fields",
            return_value=["foo", "bar", "baz"],
        )
        assert Indexed.is_directly_defined("hello") is False
        mock_get_directly_defined_fields.assert_called_once()
        assert Indexed.is_directly_defined("baz") is True
