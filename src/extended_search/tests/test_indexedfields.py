import pytest

from extended_search.index import BaseField  # AbstractBaseField,
from extended_search.index import (
    DWIndexedField,
    IndexedField,
    MultiQueryIndexedField,
    RelatedFields,
)

# from extended_search.types import AnalysisType

# @pytest.mark.xfail
# class TestAbstractBaseField:
#     def test_init_params_accepted_defaults_and_all_saved(self):
#         field = AbstractBaseField("foo")
#         assert field.field_name == "foo"
#         assert field.model_field_name == field.field_name
#         assert field.boost == 1.0

#         field = AbstractBaseField("foo", model_field_name="bar", boost=33.7)
#         assert field.field_name == "foo"
#         assert field.model_field_name == "bar"
#         assert field.boost == 33.7

#         field = AbstractBaseField("foo", test="baz")
#         with pytest.raises(AttributeError):
#             assert field.test == "baz"

#     def test_get_base_mapping_object_format(self):
#         field = AbstractBaseField("foo")
#         assert {
#             "name": field.field_name,
#             "model_field_name": field.model_field_name,
#             "boost": field.boost,
#             "parent_model_field": None,
#         } == field._get_base_mapping_object()

#     def test_get_mapping_uses_get_base_mapping_object(self):
#         field = AbstractBaseField("foo")
#         assert field.get_mapping() == field._get_base_mapping_object()

#     def test_mapping_property_uses_get_mapping_method(self, mocker):
#         mock_func = mocker.patch(
#             "extended_search.index.AbstractBaseField.get_mapping",
#             return_value={"name": "foo"},
#         )
#         field = AbstractBaseField("foo")
#         mapping = field.mapping
#         mock_func.assert_called_once()
#         assert mapping == field.get_mapping()


class TestBaseField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = BaseField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name

        field = BaseField("foo", model_field_name="bar")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"

    @pytest.mark.xfail
    def test_get_field(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_definition_model(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_value(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_attname(self):
        raise AssertionError()


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

    @pytest.mark.xfail
    def test_get_analyzers(self):
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

    @pytest.mark.xfail
    def test_get_analyzers(self):
        raise AssertionError()


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

    @pytest.mark.xfail
    def test_get_analyzers(self):
        raise AssertionError()


class TestRelatedFields:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = RelatedFields("foo", ["bar", "baz"])
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.fields == ["bar", "baz"]

    @pytest.mark.xfail
    def test_get_field(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_definition_model(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_value(self):
        raise AssertionError()

    @pytest.mark.xfail
    def test_get_select_on_queryset(self):
        raise AssertionError()
