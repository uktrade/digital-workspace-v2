import pytest

from extended_search.index import AutocompleteField  # AbstractBaseField,
from extended_search.index import (
    BaseField,
    DWIndexedField,
    FilterField,
    IndexedField,
    ModelFieldNameMixin,
    MultiQueryIndexedField,
    RelatedFields,
    SearchField,
    get_indexed_field_name,
)
from extended_search.types import AnalysisType


from extended_search import settings


class Base:
    def __init__(self, *args, **kwargs) -> None:
        ...


class MixedIn(ModelFieldNameMixin, Base):
    ...


class TestModelFieldNameMixin:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = MixedIn("foo")
        assert field.model_field_name == "foo"
        assert field.parent_field is None

        field = MixedIn("foo", model_field_name="bar")
        assert field.model_field_name == "bar"
        assert field.parent_field is None

        field = MixedIn("foo", model_field_name="bar", parent_field="baz")
        assert field.model_field_name == "bar"
        assert field.parent_field == "baz"

    def test_get_field(self):
        raise AssertionError()

    def test_get_definition_model(self):
        raise AssertionError()

    def test_get_value(self):
        raise AssertionError()

    def test_is_relation_of(self):
        raise AssertionError()

    def test_get_base_field(self):
        raise AssertionError()

    def test_get_base_model_field_name(self):
        raise AssertionError()

    def test_get_full_model_field_name(self):
        raise AssertionError()


class TestBaseField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = BaseField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.parent_field is None

        field = BaseField("foo", model_field_name="bar")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"
        assert field.parent_field is None

        field = BaseField("foo", model_field_name="bar", parent_field="baz")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"
        assert field.parent_field == "baz"

    def test_basefield_inherits_from_modelfieldnamemixin(self):
        raise AssertionError()


class TestSearchField:
    def test_searchfield_inherits_from_basefield(self):
        raise AssertionError()

    def test_searchfield_inherits_from_wagtail_searchfield(self):
        raise AssertionError()


class TestAutocompleteField:
    def test_autocompletefield_inherits_from_basefield(self):
        raise AssertionError()

    def test_autocompletefield_inherits_from_wagtail_autocompletefield(self):
        raise AssertionError()


class TestFilterField:
    def test_filterfield_inherits_from_basefield(self):
        raise AssertionError()

    def test_filterfield_inherits_from_wagtail_filterfield(self):
        raise AssertionError()


class TestRelatedFields:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = RelatedFields("foo", ["bar", "baz"])
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.fields == ["bar", "baz"]

    def test_generate_fields(self):
        raise AssertionError()

    def test_get_select_on_queryset(self):
        raise AssertionError()

    def test_relatedfields_inherits_from_modelfieldnamemixin(self):
        ...

    def test_get_related_fields_returns_extended_relatedfields(self, mocker):
        mock_func = mocker.patch(
            "extended_search.index.Indexed._get_indexed_fields_from_mapping",
            return_value=["SearchFieldObject <bar>"],
        )
        result = RelatedFields.generate_fields("foo", [{"field_name": "baz"}])
        mock_func.assert_called_once_with({"field_name": "baz"})
        assert type(result) == list
        assert type(result[0]) == RelatedFields
        assert result[0].field_name == "foo"
        assert result[0].fields == ["SearchFieldObject <bar>"]

        mock_func.reset_mock()
        result = RelatedFields.generate_fields(
            "foo",
            [{"field_name": "baz"}, {"field_name": "bam"}, {"field_name": "foobar"}],
        )
        assert mock_func.call_count == 3
        assert len(result[0].fields) == 3


class TestIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = IndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert field.search_kwargs == {}
        assert not field.autocomplete
        assert field.autocomplete_kwargs == {}
        assert not field.filter
        assert field.filter_kwargs == {}

        field = IndexedField(
            "foo",
            boost=44.9,
            search=True,
            filter=True,
            autocomplete=True,
            search_kwargs={"foo": 99},
            filter_kwargs={"bar": True},
            autocomplete_kwargs={"baz": "foobar"},
        )
        assert field.boost == 44.9
        assert field.search
        assert field.search_kwargs == {"foo": 99}
        assert field.filter
        assert field.filter_kwargs == {"bar": True}
        assert field.autocomplete
        assert field.autocomplete_kwargs == {"baz": "foobar"}

    def test_get_autocomplete_search_fields_returns_extended_autocompletefield(self):
        result = IndexedField.generate_autocomplete_fields("foo")
        assert type(result) == list
        assert type(result[0]) == AutocompleteField
        assert result[0].field_name == "foo"

    def test_get_filterable_search_fields_returns_wagtail_filterfield(self):
        result = IndexedField.generate_filter_fields("foo")
        assert type(result) == list
        assert type(result[0]) == FilterField
        assert result[0].field_name == "foo"

    def test_get_searchable_search_fields_returns_extended_searchfields(self, mocker):
        mock_fieldname = mocker.patch(
            "extended_search.query_builder.get_indexed_field_name",
            return_value="bar",
        )
        mock_analyzer = mocker.patch(
            "extended_search.index.Indexed._get_analyzer_name",
            return_value="baz",
        )
        result = IndexedField.generate_search_fields("foo", [], 3.2)
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

    def test_get_searchable_search_fields_returns_field_per_analyzer(self, mocker):
        mocker.patch(
            "extended_search.query_builder.get_indexed_field_name",
            return_value="bar",
        )
        mocker.patch(
            "extended_search.index.Indexed._get_analyzer_name",
            return_value="baz",
        )
        assert len(IndexedField.generate_search_fields("foo", [], boost=22.5)) == 1
        assert len(IndexedField.generate_search_fields("foo", ["first"])) == 1
        assert len(IndexedField.generate_search_fields("foo", ["first", "second"])) == 2
        assert (
            len(
                IndexedField.generate_search_fields("foo", ["first", "second", "three"])
            )
            == 3
        )

    def test_generate_fields(self):
        raise AssertionError()

    def test_generate_search_fields(self):
        raise AssertionError()

    def test_generate_autocomplete_fields(self):
        raise AssertionError()

    def test_generate_filter_fields(self):
        raise AssertionError()

    def test_get_search_field_variants(self):
        raise AssertionError()

    def test_get_autocomplete_field_variants(self):
        raise AssertionError()

    def test_get_filter_field_variants(self):
        raise AssertionError()


class TestMultiQueryIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = MultiQueryIndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy
        assert not field.tokenized
        assert not field.explicit

        field = MultiQueryIndexedField(
            "foo",
            explicit=True,
            tokenized=True,
            fuzzy=True,
        )
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert field.explicit
        assert field.tokenized
        assert field.fuzzy

    def test_init_params_set_search_param_when_needed(self):
        field = MultiQueryIndexedField("foo", tokenized=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert field.tokenized
        assert not field.fuzzy

        field = MultiQueryIndexedField("foo", explicit=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert field.explicit
        assert not field.tokenized
        assert not field.fuzzy

        field = MultiQueryIndexedField("foo", fuzzy=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert not field.tokenized
        assert field.fuzzy

    def test_get_search_analyzers(self):
        raise AssertionError()

    def test_get_autocomplete_analyzers(self):
        raise AssertionError()

    def test_get_filter_analyzers(self):
        raise AssertionError()

    def test_get_search_field_variants(self, mocker):
        mock_get_name = mocker.patch(
            "extended_search.index.get_indexed_field_name",
            return_value="--field-name--",
        )
        mock_analyzers = mocker.patch(
            "extended_search.index.MultiQueryIndexedField.get_search_analyzers",
            return_value=[],
        )

        field = MultiQueryIndexedField("foo")
        assert field.get_search_field_variants() == []
        mock_analyzers.assert_called_once_with()
        mock_get_name.assert_not_called()

        mock_analyzers.reset_mock()
        mock_analyzers.return_value = [AnalysisType.TOKENIZED]
        assert field.get_search_field_variants() == [
            (
                "--field-name--",
                {
                    "es_extra": {
                        "analyzer": settings.extended_search_settings["analyzers"][
                            AnalysisType.TOKENIZED.value
                        ]["es_analyzer"]
                    }
                },
            )
        ]
        mock_analyzers.assert_called_once_with()
        mock_get_name.assert_called_once_with("foo", AnalysisType.TOKENIZED)


class TestDWIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = DWIndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy
        assert not field.tokenized
        assert not field.explicit
        assert not field.keyword

    def test_init_params_set_search_param_when_needed(self):
        field = DWIndexedField("foo", keyword=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert not field.tokenized
        assert field.keyword
        assert not field.fuzzy

    def test_get_search_analyzers(self, mocker):
        mocker.patch(
            "extended_search.index.MultiQueryIndexedField.get_search_analyzers",
            return_value=set(),
        )
        field = DWIndexedField("foo", keyword=False)
        assert field.get_search_analyzers() == set()
        field = DWIndexedField("foo", keyword=True)
        assert field.get_search_analyzers() == {AnalysisType.KEYWORD}


class TestGetIndexedField:
    @pytest.mark.django_db
    def test_get_indexed_field_name(self):
        with pytest.raises(AttributeError):
            get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert get_indexed_field_name("foo", analyzer) == "foo"

        settings.settings_singleton["analyzers"][analyzer.value][
            "index_fieldname_suffix"
        ] = "bar"
        settings.extended_search_settings = settings.settings_singleton.to_dict()

        assert (
            settings.settings_singleton["analyzers"][analyzer.value][
                "index_fieldname_suffix"
            ]
            == "bar"
        )
        assert get_indexed_field_name("foo", analyzer) == "foobar"

        settings.settings_singleton["analyzers"][analyzer.value][
            "index_fieldname_suffix"
        ] = ""
        settings.extended_search_settings = settings.settings_singleton.to_dict()
