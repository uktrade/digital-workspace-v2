import copy
from collections import ChainMap
from types import NoneType

import pytest
from wagtail.search import index

from extended_search.index import BaseField, SearchField
from extended_search.models import Setting
from extended_search.settings import (
    DEFAULT_SETTINGS,
    NESTING_SEPARATOR,
    SETTINGS_KEY,
    NestedChainMap,
    SearchSettings,
    extended_search_settings,
    get_settings_field_key,
    settings_singleton,
)


class TestDefaults:
    def test_required_keys_set(self):
        assert "boost_parts" in DEFAULT_SETTINGS
        assert "analyzers" in DEFAULT_SETTINGS
        assert "query_types" in DEFAULT_SETTINGS["boost_parts"]
        assert "analyzers" in DEFAULT_SETTINGS["boost_parts"]
        assert "fields" in DEFAULT_SETTINGS["boost_parts"]
        assert "extras" in DEFAULT_SETTINGS["boost_parts"]
        assert "phrase" in DEFAULT_SETTINGS["boost_parts"]["query_types"]
        assert "query_and" in DEFAULT_SETTINGS["boost_parts"]["query_types"]
        assert "query_or" in DEFAULT_SETTINGS["boost_parts"]["query_types"]
        assert "tokenized" in DEFAULT_SETTINGS["boost_parts"]["analyzers"]
        assert "explicit" in DEFAULT_SETTINGS["boost_parts"]["analyzers"]
        assert "tokenized" in DEFAULT_SETTINGS["analyzers"]
        assert "explicit" in DEFAULT_SETTINGS["analyzers"]
        assert "keyword" in DEFAULT_SETTINGS["analyzers"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "query_and" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "query_or" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "query_and" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "query_or" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"]
        assert isinstance(
            DEFAULT_SETTINGS["boost_parts"]["query_types"]["phrase"], float
        )
        assert isinstance(
            DEFAULT_SETTINGS["boost_parts"]["query_types"]["query_and"], float
        )
        assert isinstance(
            DEFAULT_SETTINGS["boost_parts"]["query_types"]["query_or"], float
        )
        assert isinstance(
            DEFAULT_SETTINGS["boost_parts"]["analyzers"]["explicit"], float
        )
        assert isinstance(
            DEFAULT_SETTINGS["boost_parts"]["analyzers"]["tokenized"], float
        )
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["tokenized"]["es_analyzer"], str
        )
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["tokenized"]["index_fieldname_suffix"],
            (str, NoneType),
        )
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"], list
        )
        assert isinstance(DEFAULT_SETTINGS["analyzers"]["explicit"]["es_analyzer"], str)
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["explicit"]["index_fieldname_suffix"],
            (str, NoneType),
        )
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"], list
        )
        assert isinstance(DEFAULT_SETTINGS["analyzers"]["keyword"]["es_analyzer"], str)
        assert isinstance(
            DEFAULT_SETTINGS["analyzers"]["keyword"]["index_fieldname_suffix"],
            (str, NoneType),
        )
        assert isinstance(DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"], list)
        for v in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]:
            assert isinstance(v, str)
            assert v in ["phrase", "query_and", "query_or"]
        for v in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]:
            assert isinstance(v, str)
            assert v in ["phrase", "query_and", "query_or"]
        for v in DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"]:
            assert isinstance(v, str)
            assert v in ["phrase", "query_and", "query_or"]


class TestNestedChainMap:
    def test_init(self, mocker):
        mock_parent = mocker.patch(
            "extended_search.settings.ChainMap.__init__", return_value=None
        )
        instance = NestedChainMap(prefix="x", nesting_separator="y", anything="z")
        mock_parent.assert_called_once_with(anything="z")
        assert instance.prefix == "x"
        assert instance.nesting_separator == "y"
        instance = NestedChainMap()
        assert instance.nesting_separator == NESTING_SEPARATOR

    def test_getitem(self, mocker):
        mock_missing = mocker.patch(
            "extended_search.settings.NestedChainMap.__missing__",
            return_value="--MISSING--",
        )
        map1 = {"foo": "a", "bar": "b"}
        map2 = {"foo": 2, "foobar": "c"}
        instance = NestedChainMap(map1, map2)
        assert instance["foo"] == "a"
        assert instance["bar"] == "b"
        assert instance["foobar"] == "c"
        map1["baz"] = "d"
        assert instance["baz"] == "d"
        map2["nest"] = {"test": "try"}
        assert instance["nest"]["test"] == "try"
        map1["nest"] = {"test": "attempt"}
        assert instance["nest"]["test"] == "attempt"
        assert instance["a"] == "--MISSING--"
        mock_missing.assert_called_once_with("a")
        mock_missing.reset_mock()
        assert instance["nest"]["b"] == "--MISSING--"
        mock_missing.assert_called_once_with("b")
        mock_prefix = mocker.patch(
            "extended_search.settings.NestedChainMap._get_prefixed_key_name",
            return_value="foo__bar",
        )
        sub_instance = instance["nest"]
        mock_prefix.assert_called_once_with("nest", None)
        assert sub_instance.prefix == "foo__bar"

    def test_missing(self, mocker):
        mocker.patch(
            "extended_search.settings.NestedChainMap._get_all_prefixed_keys_from_nested_maps",
            return_value=["a", "b"],
        )
        mock_getitem = mocker.patch(
            "extended_search.settings.NestedChainMap._getitem_from_nested_maps_for_prefixed_key",
            return_value="--foobar--",
        )
        map1 = {"foo": "a", "bar": "b"}
        map2 = {"foo": 2, "foobar": "c"}
        instance = NestedChainMap(map1, map2)
        assert instance.all_keys() == ["a", "b"]
        with pytest.raises(KeyError):
            instance["baz"]
        mock_getitem.assert_not_called()
        assert instance["a"] == "--foobar--"
        mock_getitem.assert_called_once_with("a", instance)

    def test_get_prefixed_key_name(self):
        instance = NestedChainMap()
        assert instance.nesting_separator == NESTING_SEPARATOR
        assert NESTING_SEPARATOR == "__"
        assert instance._get_prefixed_key_name("foo", None) == "foo"
        assert instance._get_prefixed_key_name("foo", "bar") == "bar__foo"
        instance = NestedChainMap(nesting_separator="**")
        assert instance._get_prefixed_key_name("foo", "bar") == "bar**foo"

    def test_get_all_prefixed_keys_from_nested_maps(self, mocker):
        map1 = {"foo": "a", "bar": "b", "baz": {"nest": "test"}}
        map2 = {"foo": 2, "foobar": "c"}
        instance = NestedChainMap()
        assert [
            "foo",
            "foobar",
        ] == instance._get_all_prefixed_keys_from_nested_maps(map2, None)
        assert [
            "foo",
            "bar",
            "baz__nest",
        ] == instance._get_all_prefixed_keys_from_nested_maps(map1, None)

        mock_name = mocker.patch(
            "extended_search.settings.NestedChainMap._get_prefixed_key_name",
            side_effect=["--one--", "--two--"],
        )
        assert [
            "--one--",
            "--two--",
        ] == instance._get_all_prefixed_keys_from_nested_maps(map2, None)
        assert mock_name.call_count == 2

    def test_all_keys(self, mocker):
        mock_all = mocker.patch(
            "extended_search.settings.NestedChainMap._get_all_prefixed_keys_from_nested_maps",
            return_value=["--one--", "--two--"],
        )
        map1 = {"foo": "a", "bar": "b", "baz": {"nest": "test"}}
        map2 = {"foo": 2, "foobar": "c"}
        instance = NestedChainMap(map1, map2)
        assert [
            "--one--",
            "--two--",
        ] == instance.all_keys()
        mock_all.assert_called_with(instance, "")

    def test_get_item_from_nested_maps_for_prefixed_key(self, mocker):
        instance = NestedChainMap()
        assert instance.nesting_separator == NESTING_SEPARATOR
        assert NESTING_SEPARATOR == "__"
        test_dict = {"key": "--val--"}
        assert "--val--" == instance._getitem_from_nested_maps_for_prefixed_key(
            "key", test_dict
        )
        with pytest.raises(KeyError):
            instance._getitem_from_nested_maps_for_prefixed_key("key2", test_dict)

        sub_dict = {"subkey": "--val--"}
        test_dict = {"key": sub_dict}
        assert sub_dict == instance._getitem_from_nested_maps_for_prefixed_key(
            "key", test_dict
        )
        with pytest.raises(KeyError):
            instance._getitem_from_nested_maps_for_prefixed_key("subkey", test_dict)
        assert "--val--" == instance._getitem_from_nested_maps_for_prefixed_key(
            "key__subkey", test_dict
        )
        super_dict = {"newkey": test_dict}
        assert "--val--" == instance._getitem_from_nested_maps_for_prefixed_key(
            "newkey__key__subkey", super_dict
        )


class TestSearchSettings:
    def test_init(self, settings):
        assert SETTINGS_KEY == "SEARCH_EXTENDED"
        settings.SEARCH_EXTENDED = {"--settings--": None}
        instance = SearchSettings()
        assert len(instance.maps) == 5
        assert instance.maps[4] == DEFAULT_SETTINGS
        assert instance.defaults == instance.maps[4]
        assert instance.maps[3] == {"--settings--": None}
        assert instance.django_settings == instance.maps[3]
        assert instance.maps[2] == {"boost_parts": {"fields": {}}}
        assert instance.fields == instance.maps[2]
        assert instance.maps[1] == {}
        assert instance.env_vars == instance.maps[1]
        assert instance.maps[0] == {}
        assert instance.db_vars == instance.maps[0]

        instance = SearchSettings(prefix="--anything--")
        assert instance.maps == [{}]
        assert not hasattr(instance, "defaults")
        assert not hasattr(instance, "django_settings")
        assert not hasattr(instance, "fields")
        assert not hasattr(instance, "env_vars")
        assert not hasattr(instance, "db_vars")

    def test_get_all_indexed_fields(self, mocker):
        mock_get_models = mocker.patch("extended_search.settings.get_indexed_models")
        instance = SearchSettings()
        assert {} == instance._get_all_indexed_fields()

        mock_model_1 = mocker.MagicMock()
        mock_model_2 = mocker.MagicMock()
        mock_searchfield_1 = mocker.MagicMock(spec=SearchField)
        mock_searchfield_1.get_definition_model.return_value = "--model--"
        mock_searchfield_2 = mocker.MagicMock(spec=SearchField)
        mock_searchfield_2.get_definition_model.return_value = "--model--"
        mock_searchfield_3 = mocker.MagicMock(spec=SearchField)
        mock_searchfield_3.get_definition_model.return_value = "--second-model--"
        mock_model_1.get_search_fields.return_value = [
            mock_searchfield_1,
            mock_searchfield_2,
            mock_searchfield_2,
        ]
        mock_model_2.get_search_fields.return_value = [
            mock_searchfield_3,
        ]
        mock_get_models.return_value = [
            mock_model_1,
            mock_model_2,
        ]
        assert {
            "--model--": set(
                [
                    mock_searchfield_1,
                    mock_searchfield_2,
                ]
            ),
            "--second-model--": set(
                [
                    mock_searchfield_3,
                ]
            ),
        } == instance._get_all_indexed_fields()

    def test_initialise_field_dict(self, mocker):
        mocker.patch(
            "extended_search.settings.get_settings_field_key",
            return_value="--settings-field-key--",
        )
        mock_get_fields = mocker.patch(
            "extended_search.settings.SearchSettings._get_all_indexed_fields"
        )
        mock_model = mocker.MagicMock()
        mock_searchfield = mocker.MagicMock(spec=BaseField)
        mock_searchfield.boost = 22
        mock_get_fields.return_value = {
            mock_model: set(
                [
                    mock_searchfield,
                ]
            ),
        }
        instance = SearchSettings()
        instance.initialise_field_dict()
        assert {
            "boost_parts": {
                "fields": {
                    "--settings-field-key--": 22,
                }
            }
        } == instance.fields

        del mock_searchfield.boost
        instance = SearchSettings()
        instance.initialise_field_dict()
        assert {
            "boost_parts": {
                "fields": {
                    "--settings-field-key--": 1.0,
                }
            }
        } == instance.fields

    def test_initialise_env_dict(self, mocker):
        mock_env = mocker.patch("extended_search.settings.env")
        mocker.patch(
            "extended_search.settings.NestedChainMap._get_all_prefixed_keys_from_nested_maps",
            return_value=[],
        )  # for all_keys
        instance = SearchSettings()
        assert instance.env_vars == {}
        instance.initialise_env_dict()
        assert instance.env_vars == {}

        mock_env.side_effect = ["value", "other"]
        mocker.patch(
            "extended_search.settings.NestedChainMap._get_all_prefixed_keys_from_nested_maps",
            return_value=["top__middle__key", "top__second"],
        )  # for all_keys
        instance = SearchSettings()
        instance.initialise_env_dict()
        assert mock_env.call_count == 2
        assert instance.env_vars == {
            "top": {
                "middle": {"key": "value"},
                "second": "other",
            },
        }
        mock_env.assert_any_call(f"{SETTINGS_KEY}__top__middle__key")
        mock_env.assert_any_call(f"{SETTINGS_KEY}__top__second")
        assert mock_env.call_count == 2

    @pytest.mark.django_db
    def test_initialise_db_dict(self):
        instance = SearchSettings()
        assert instance.db_vars == {}
        assert Setting.objects.all().count() == 0
        instance.initialise_db_dict()
        assert instance.db_vars == {}

        Setting.objects.create(key="test.field.name", value="test")
        assert Setting.objects.all().count() == 1
        instance.initialise_db_dict()
        assert instance.db_vars == {"test.field.name": "test"}

        instance.db_vars = {}
        Setting.objects.all().delete()
        Setting.objects.create(
            key="boost_parts__fields__test.field.name", value="trial"
        )
        assert Setting.objects.all().count() == 1
        instance.initialise_db_dict()
        assert instance.db_vars == {
            "boost_parts": {"fields": {"test.field.name": "trial"}},
        }

    def test_singleton(self):
        instance = SearchSettings()
        assert isinstance(instance, SearchSettings)
        assert isinstance(settings_singleton, SearchSettings)
        assert instance.defaults == settings_singleton.defaults
        instance["test"] = "foo"
        assert "test" in instance
        assert instance["test"] == "foo"
        assert "test" not in settings_singleton
        settings_singleton["test"] = "bar"
        assert "test" in settings_singleton
        assert settings_singleton["test"] == "bar"
        from extended_search.settings import settings_singleton as second_import

        assert "test" in second_import
        assert second_import["test"] == settings_singleton["test"]

    def test_to_dict(self):
        instance = SearchSettings()
        assert not isinstance(instance, dict)
        assert isinstance(instance.to_dict(), dict)
        assert isinstance(extended_search_settings, dict)

        def test_values(input):
            output = []
            if isinstance(input, ChainMap):
                raise AssertionError(f"{input} is a ChainMap")
            elif isinstance(input, dict):
                for v in input.values():
                    output += test_values(v)
            elif not isinstance(input, (str, bool, list, int, float)):
                raise AssertionError(f"{input} is not a base type: {type(input)}")
            else:
                raise AssertionError(f"{input} is not recognised")

    def test_updated_settings_affect_exported_dict(self):
        from extended_search import settings  # 1
        from extended_search.settings import extended_search_settings  # 2

        original_settings = copy.deepcopy(settings.extended_search_settings)
        assert original_settings == settings.extended_search_settings  # 1
        assert original_settings == extended_search_settings  # 2

        # update a setting
        settings.settings_singleton["boost_parts"]["fields"]["--test--"] = 666.66

        # no exported dicts changed yet
        assert original_settings == settings.extended_search_settings  # 1
        assert original_settings == extended_search_settings  # 2

        # update the export
        assert original_settings != settings.settings_singleton.to_dict()
        settings.extended_search_settings = settings_singleton.to_dict()

        # exported module dict changed
        assert (
            original_settings != settings.extended_search_settings
        )  # <-- in general use this style import
        # ... but exported dict still not changed yet :'(
        assert original_settings == extended_search_settings

        # re-import
        from extended_search.settings import extended_search_settings

        # all updated now
        assert original_settings != extended_search_settings
        assert extended_search_settings == settings.extended_search_settings
        assert settings_singleton.to_dict() == settings.extended_search_settings


class TestGetSettingsFieldKey:
    def test_get_settings_field_key(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model._meta.app_label = "--app-label-1--"
        mock_model._meta.model_name = "--model-name-1--"
        mock_searchfield_1 = mocker.MagicMock(spec=index.BaseField)
        mock_searchfield_1.field_name = "--field-name-1--"
        mock_searchfield_1.get_full_model_field_name = mocker.MagicMock(
            return_value="--full-model-field-name-1--"
        )
        mock_searchfield_2 = mocker.MagicMock(spec=BaseField)
        mock_searchfield_2.field_name = "--field-name-2--"
        mock_searchfield_2.get_full_model_field_name = mocker.MagicMock(
            return_value="--full-model-field-name-2--"
        )

        field_key_1 = get_settings_field_key(mock_model, mock_searchfield_1)
        mock_searchfield_1.get_full_model_field_name.assert_not_called()
        assert field_key_1 == "--app-label-1--.--model-name-1--.--field-name-1--"

        field_key_2 = get_settings_field_key(mock_model, mock_searchfield_2)
        mock_searchfield_2.get_full_model_field_name.assert_called_once_with()
        assert (
            field_key_2
            == "--app-label-1--.--model-name-1--.--full-model-field-name-2--"
        )
