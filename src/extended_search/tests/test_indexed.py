import pytest
from extended_search.index import Indexed


class TestIndexed:
    @pytest.mark.xfail
    def test_get_indexed_fields_uses_submethod(self, mocker):
        mock_submethod = mocker.patch(
            "extended_search.index.Indexed._get_indexed_fields_from_mapping"
        )
        Indexed.get_indexed_fields()
        mock_submethod.assert_called_once_with("foo")

    @pytest.mark.xfail
    def test_get_indexed_fields_returns_all_indexed_and_related_fields_and_no_others(
        self, mocker
    ):
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
    def test_get_indexed_fields_uses_generate_fields(self, mocker):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_search_fields_uses_indexed_fields_and_search_fields_attrs(
        self, mocker
    ):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_search_fields_allows_indexed_fields_to_override_parent_fields(
        self, mocker
    ):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_search_fields_uses_all_parent_indexed_model_fields(self, mocker):
        raise AssertionError()


class TestModuleFunctions:
    @pytest.mark.xfail
    def test_get_indexed_models(self, mocker):
        raise AssertionError()

    @pytest.mark.xfail
    def test_class_is_indexed(self, mocker):
        raise AssertionError()
