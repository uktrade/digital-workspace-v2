import pytest

from content.models import ContentPage
from extended_search.managers import (
    get_indexed_field_name,
    get_query_for_model,
)
from extended_search.models import Setting
from extended_search.settings import extended_search_settings
from extended_search.types import AnalysisType


class TestManagersInit:
    @pytest.mark.django_db
    def test_get_indexed_field_name(self):
        with pytest.raises(AttributeError):
            get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert get_indexed_field_name("foo", analyzer) == "foo"
        assert get_indexed_field_name("foo", analyzer, "baz") == "baz.foo"

        Setting.objects.create(
            key=f"analyzers__{analyzer.value}__index_fieldname_suffix", value="bar"
        )
        assert (
            extended_search_settings[
                f"analyzers__{analyzer.value}__index_fieldname_suffix"
            ]
            == "bar"
        )
        assert get_indexed_field_name("foo", analyzer) == "foobar"
        assert get_indexed_field_name("foo", analyzer, "baz") == "baz.foobar"

    def test_get_query_for_model(self, mocker):
        mock_map = mocker.patch(
            "extended_search.managers.index.ModelIndexManager.get_mapping",
            return_value=[],
        )
        mock_q = mocker.patch(
            "extended_search.managers.query_builder.QueryBuilder._get_search_query_from_mapping",
            return_value=[],
        )
        assert get_query_for_model(ContentPage, "query") is None
        mock_map.assert_called_once_with()

        mock_map.return_value = ["--one--"]
        mock_q.return_value = "--query--"
        assert get_query_for_model(ContentPage, "query") == "--query--"
        mock_q.assert_called_once_with("query", ContentPage, "--one--")

    def test_get_search_query(self, mocker):
        mocker.patch(
            "wagtail.search.index.get_indexed_models",
            return_value=[],
        )
        mocker.patch(
            "extended_search.managers.get_query_for_model",
            return_value=[],
        )
        raise AssertionError()
