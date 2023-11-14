from types import NoneType

import pytest
from extended_search.models import Setting
from extended_search.settings import (
    DEFAULT_SETTINGS,
    NESTING_SEPARATOR,
    SETTINGS_KEY,
    NestedChainMap,
    SearchSettings,
    extended_search_settings,
)
from wagtail.search.index import SearchField


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
        assert "proximity" in DEFAULT_SETTINGS["analyzers"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["tokenized"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["explicit"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "query_types" in DEFAULT_SETTINGS["analyzers"]["keyword"]
        assert "es_analyzer" in DEFAULT_SETTINGS["analyzers"]["proximity"]
        assert "index_fieldname_suffix" in DEFAULT_SETTINGS["analyzers"]["proximity"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "query_and" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "query_or" in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "query_and" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "query_or" in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]
        assert "phrase" in DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"]
        assert type(DEFAULT_SETTINGS["boost_parts"]["query_types"]["phrase"]) == float
        assert (
            type(DEFAULT_SETTINGS["boost_parts"]["query_types"]["query_and"]) == float
        )
        assert type(DEFAULT_SETTINGS["boost_parts"]["query_types"]["query_or"]) == float
        assert type(DEFAULT_SETTINGS["boost_parts"]["analyzers"]["explicit"]) == float
        assert type(DEFAULT_SETTINGS["boost_parts"]["analyzers"]["tokenized"]) == float
        assert type(DEFAULT_SETTINGS["analyzers"]["tokenized"]["es_analyzer"]) == str
        assert type(
            DEFAULT_SETTINGS["analyzers"]["tokenized"]["index_fieldname_suffix"]
        ) in (str, NoneType)
        assert type(DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]) == list
        assert type(DEFAULT_SETTINGS["analyzers"]["explicit"]["es_analyzer"]) == str
        assert type(
            DEFAULT_SETTINGS["analyzers"]["explicit"]["index_fieldname_suffix"]
        ) in (str, NoneType)
        assert type(DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]) == list
        assert type(DEFAULT_SETTINGS["analyzers"]["keyword"]["es_analyzer"]) == str
        assert type(
            DEFAULT_SETTINGS["analyzers"]["keyword"]["index_fieldname_suffix"]
        ) in (str, NoneType)
        assert type(DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"]) == list
        assert type(DEFAULT_SETTINGS["analyzers"]["proximity"]["es_analyzer"]) == str
        assert type(
            DEFAULT_SETTINGS["analyzers"]["proximity"]["index_fieldname_suffix"]
        ) in (str, NoneType)
        for v in DEFAULT_SETTINGS["analyzers"]["tokenized"]["query_types"]:
            assert type(v) == str
            assert v in ["phrase", "query_and", "query_or"]
        for v in DEFAULT_SETTINGS["analyzers"]["explicit"]["query_types"]:
            assert type(v) == str
            assert v in ["phrase", "query_and", "query_or"]
        for v in DEFAULT_SETTINGS["analyzers"]["keyword"]["query_types"]:
            assert type(v) == str
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
        assert instance.all_keys == ["a", "b"]
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
        ] == instance.all_keys
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
        mock_get_fields = mocker.patch(
            "extended_search.settings.SearchSettings._get_all_indexed_fields"
        )
        mock_model_1 = mocker.MagicMock()
        mock_model_1._meta.app_label = "--app--"
        mock_model_1._meta.model_name = "--model--"
        mock_model_2 = mocker.MagicMock()
        mock_model_2._meta.app_label = "--second-app--"
        mock_model_2._meta.model_name = "--second-model--"
        mock_searchfield_1 = mocker.MagicMock()
        mock_searchfield_1.model_field_name = "--model-field-name--"
        mock_searchfield_1.field_name = "--field-name--"
        mock_searchfield_1.boost = 22
        mock_searchfield_1.parent_model_field = "--parent-model-field--"
        mock_searchfield_2 = mocker.MagicMock()
        del mock_searchfield_2.model_field_name  # to fail hasattr
        mock_searchfield_2.field_name = "--second-field-name--"
        mock_searchfield_2.boost = 33
        mock_searchfield_2.parent_model_field = None
        mock_searchfield_3 = mocker.MagicMock()
        mock_searchfield_3.model_field_name = "--third-model-field-name--"
        mock_searchfield_3.boost = 44
        mock_searchfield_3.parent_model_field = None
        mock_searchfield_4 = mocker.MagicMock()
        mock_searchfield_4.model_field_name = "--4th-model-field-name--"
        mock_searchfield_4.field_name = "--4th-field-name--"
        mock_searchfield_4.parent_model_field = None
        del mock_searchfield_4.boost  # to fail hasattr
        mock_get_fields.return_value = {
            mock_model_1: set(
                [
                    mock_searchfield_1,
                    mock_searchfield_2,
                ]
            ),
            mock_model_2: set(
                [
                    mock_searchfield_3,
                    mock_searchfield_4,
                ]
            ),
        }
        instance = SearchSettings()
        instance.initialise_field_dict()
        assert {
            "boost_parts": {
                "fields": {
                    "--app--.--model--.--parent-model-field--.--model-field-name--": 22,
                    "--app--.--model--.--second-field-name--": 33,
                    "--second-app--.--second-model--.--third-model-field-name--": 44,
                    "--second-app--.--second-model--.--4th-model-field-name--": 1.0,
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
        assert isinstance(extended_search_settings, SearchSettings)
        assert instance.defaults == extended_search_settings.defaults
