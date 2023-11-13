from unittest.mock import call

import pytest
from wagtail.search.query import Or, PlainText

from content.models import ContentPage
from extended_search.backends.query import Filtered
from extended_search.managers import get_indexed_field_name
from extended_search.managers.query_builder import CustomQueryBuilder
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
        assert CustomQueryBuilder.get_query_for_model(ContentPage, "query") is None
        mock_map.assert_called_once_with()

        mock_map.return_value = ["--one--"]
        mock_q.return_value = "--query--"
        assert (
            CustomQueryBuilder.get_query_for_model(ContentPage, "query") == "--query--"
        )
        mock_q.assert_called_once_with("query", ContentPage, "--one--")

    def test_get_extended_models_with_indexmanager(self, mocker):
        base_model_class = mocker.Mock()
        extended_model_class = mocker.Mock()
        extended_model_class.__name__ = "extendedModel"
        extended_model_class._meta.app_label = "mock.extended"
        extended_model_class.has_indexmanager_direct_inner_class.return_value = False
        mock_get_models = mocker.patch(
            "extended_search.managers.get_indexed_models",
            return_value=[base_model_class],
        )
        mock_mro = mocker.patch(
            "extended_search.managers.inspect.getmro",
            return_value=[extended_model_class],
        )
        assert (
            CustomQueryBuilder.get_extended_models_with_indexmanager(base_model_class)
            == {}
        )

        mock_get_models.return_value = [
            base_model_class,
            extended_model_class,
        ]
        assert (
            CustomQueryBuilder.get_extended_models_with_indexmanager(base_model_class)
            == {}
        )

        extended_model_class.has_indexmanager_direct_inner_class.return_value = True
        assert (
            CustomQueryBuilder.get_extended_models_with_indexmanager(base_model_class)
            == {}
        )

        mock_mro.return_value = [extended_model_class, base_model_class]
        assert CustomQueryBuilder.get_extended_models_with_indexmanager(
            base_model_class
        ) == {"mock.extended.extendedModel": extended_model_class}

    def test_get_search_query(self, mocker):
        model_class = mocker.Mock()
        extended_model_class = mocker.Mock()
        query = "foo"  # PlainText("foo")
        mock_get_extended_models = mocker.patch(
            "extended_search.managers.get_extended_models_with_indexmanager",
            return_value={"mock.extended_model": extended_model_class},
        )
        mock_get_query = mocker.patch(
            "extended_search.managers.get_query_for_model",
            return_value=PlainText("foo"),
        )
        result = CustomQueryBuilder.get_search_query(model_class, query)
        mock_get_extended_models.assert_called_once_with(model_class)
        mock_get_query.assert_has_calls(
            [
                call(extended_model_class, query),
                call(model_class, query),
            ]
        )
        assert repr(result) == repr(
            Or(
                [
                    Filtered(
                        subquery=PlainText("foo"),
                        filters=[
                            ("content_type", "excludes", ["mock.extended_model"]),
                        ],
                    ),
                    Filtered(
                        subquery=PlainText("foo"),
                        filters=[
                            ("content_type", "contains", "mock.extended_model"),
                        ],
                    ),
                ]
            )
        )
