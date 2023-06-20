import environ
from django.conf import settings

from typing import Any, Dict

env = environ.Env()
env.read_env()

DEFAULTS = {
    "BOOST_VARIABLES": {

    },
    "ANALYZERS": {
        "TOKENIZED": {
            "es_analyzer": "snowball",
            "index_fieldname_suffix": None,
            "query_types": ["PHRASE", "QUERY_AND", "QUERY_OR",],
        },
        "EXPLICIT": {
            "es_analyzer": "simple",
            "index_fieldname_suffix": "_explicit",
            "query_types": ["PHRASE", "QUERY_AND", "QUERY_OR",],
        },
        "KEYWORD": {
            "es_analyzer": "keyword",
            "index_fieldname_suffix": "_keyword",
            "query_types": ["PHRASE"],
        },
        "PROXIMITY": {
            "es_analyzer": "simple",
            "index_fieldname_suffix": "_proximity",
        },
    }
}


class SearchExtendedSettings:

    def __getattr__(self, attr):
        # Check if set in ENV
        # setting_value = self._get_from_env(attr)
        # if setting_value:
        #     return setting_value

        # Check if present in user settings
        setting_value = self._get_from_django_settings(attr)
        if setting_value:
            return setting_value

        # Check if present in defaults
        default_value = self._get_from_defaults(attr)
        if default_value:
            return default_value

        raise AttributeError(f"No value set for SEARCH_EXTENDED['{attr}']")

    def _get_from_env(self, attr, key=None):
        setting_name = "SEARCH_EXTENDED_" + attr
        print(f">>>>>>>> {attr} <<<<<<<<<<<<< {key}")
        setting_value = env(setting_name, default=None)
        print(setting_value)
        if setting_value is not None and key is not None:
            print("WWWWTTTTTTTTTFFFFFFFFF")
            return getattr(setting_value, key, None)
        return setting_value

    def _get_from_django_settings(self, attr, key=None):
        django_settings = getattr(settings, "SEARCH_EXTENDED", {})
        if attr in django_settings:
            if key is not None:
                return getattr(django_settings[attr], key, None)
            return django_settings[attr]
        return None

    def _get_from_defaults(self, attr, key=None):
        default_value = DEFAULTS.get(attr, None)
        if default_value is not None and attr in DEFAULTS:
            if key is not None:
                return getattr(default_value, key, None)
            return default_value
        return default_value

    def get_boost_value(self, boost_key):
        """
        Get the most specifically-defined boost value for the given key
        """
        attr = "BOOST_VARIABLES"
        # Check if set in ENV
        setting_value = self._get_from_env(attr, boost_key)
        if setting_value:
            return setting_value

        # Check if present in user settings
        setting_value = self._get_from_django_settings(attr, boost_key)
        if setting_value:
            return setting_value

        # Check if present in defaults
        default_value = self._get_from_defaults(attr, boost_key)
        if default_value:
            return default_value

        return 1.0


search_extended_settings = SearchExtendedSettings()
