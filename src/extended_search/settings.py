from collections import ChainMap
from collections.abc import Mapping
import environ

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured


env = environ.Env()
env.read_env()

SETTINGS_KEY = "SEARCH_EXTENDED"
DEFAULT_SETTINGS = {
    "boost_parts": {
        "query_types": {
            "phrase": 10.0,
            "query_and": 2.5,
            "query_or": 1.0,
        },
        "analyzers": {
            "explicit": 3.5,
            "tokenized": 1.0,
        },
        "fields": {},
        "extras": {},
    },
    "analyzers": {
        "tokenized": {
            "es_analyzer": "snowball",
            "index_fieldname_suffix": None,
            "query_types": [
                "phrase",
                "query_and",
                "query_or",
            ],
        },
        "explicit": {
            "es_analyzer": "simple",
            "index_fieldname_suffix": "_explicit",
            "query_types": [
                "phrase",
                "query_and",
                "query_or",
            ],
        },
        "keyword": {
            "es_analyzer": "no_spaces",
            "index_fieldname_suffix": "_keyword",
            "query_types": ["phrase"],
        },
        "proximity": {  # @TODO think this needs cleanup to work more like Fuzzy - i.e. built into query but analyzed as a FileterField
            "es_analyzer": "keyword",
            "index_fieldname_suffix": None,
        },
    },
}

DEFAULTS = DEFAULT_SETTINGS


class SettingNotFound(Exception):
    pass


class Settings(ChainMap):
    """
    Allows nested ChainMap functionality, with settings-specific overrides
    Approach taken from https://github.com/neutrinoceros/deep_chainmap

    Settings are returned in priority order (high to low):
    1. DB settings
    2. ENV variables
    3. Model IndexField definitions
    4. Django settings
    5. Defaults in app

    Note that settings in the DB, IndexField and ENV are set one by one, while
    those in the Django Settings and the defaults are created as (either full
    or partial/sparse) dicts.
    """

    def __init__(self, *args, prefix=None, **kwargs):
        self.prefix = prefix
        if prefix is not None:
            # This instance is a sub-map used for the recursive / nested structure
            return super().__init__(*args, **kwargs)

        self.defaults = DEFAULT_SETTINGS
        self.django_settings = self.get_file_settings()
        return super().__init__(self.django_settings, self.defaults)

    def __getitem__(self, key):
        """
        Handles nested Chainmap functionality, and also breaks out the
        leaf-node override method
        """
        submaps = [mapping for mapping in self.maps if key in mapping]
        if not submaps:
            return self.__missing__(key)
        if isinstance(submaps[0][key], Mapping):
            return Settings(
                *(submap[key] for submap in submaps), prefix=self._get_prefixed_key(key)
            )
        if value := self.get_overriden_single_item(key):
            return value
        return super().__getitem__(key)

    def _get_prefixed_key(self, key):
        """
        Consistent method for naming leaf-node keys using `__` to separate dict
        levels from the main settings, useful for ENV settings e.g.
        "SEARCH_EXTENDED": {
            "boost_parts":{
                "search_phrase": 2.5
            }
        }
        -->
        SEARCH_EXTENDED__boost_parts__search_phrase=2.5
        """
        if self.prefix:
            return f"{self.prefix}__{key}"
        return key

    def get_overriden_single_item(self, key):
        """
        Allows for settings defined as single items to jump into the overrides,
        either from ENV or from e.g. field definitions
        """
        print("trying to get overridable setting", self._get_prefixed_key(key))
        # get from DB
        # or
        # get from ENV
        try:
            return env(self._get_prefixed_key(key))
        except ImproperlyConfigured:
            ...
        # or
        # get from field level (if applicable)
        if "__" in key:
            print("field key??", key)

        # Fall back to overall settings ChainMap (i.e. from file or default values)
        return None

    def get_file_settings(self):
        return getattr(django_settings, SETTINGS_KEY, {})


class SearchExtendedSettings:
    def __getattr__(self, attr):
        # # Check if set in ENV
        # try:
        #     setting_value = self._get_from_env(attr)
        #     return setting_value
        # except SettingNotFound:

        # Check if present in user settings
        try:
            setting_value = self._get_from_django_settings(attr)
            return setting_value
        except SettingNotFound:
            # Check if present in defaults
            try:
                default_value = self._get_from_defaults(attr)
                return default_value
            except SettingNotFound:
                raise AttributeError(f"No value set for SEARCH_EXTENDED['{attr}']")

    def _get_from_env(self, attr, key=None):
        setting_name = "SEARCH_EXTENDED_" + attr
        try:
            setting_value = env(setting_name)
        except ImproperlyConfigured:
            raise SettingNotFound()

        if key is not None:
            return getattr(setting_value, key)
        return setting_value

    def _get_from_django_settings(self, attr, key=None):
        file_settings = getattr(django_settings, "SEARCH_EXTENDED", {})
        if attr in file_settings:
            if key is not None:
                return getattr(file_settings[attr], key, None)
            return file_settings[attr]
        raise SettingNotFound()

    def _get_from_defaults(self, attr, key=None):
        default_value = DEFAULTS.get(attr, None)
        if default_value is None:
            raise SettingNotFound()

        if attr in DEFAULTS:
            if key is not None:
                return getattr(default_value, key, None)
            return default_value
        return default_value

    def _get_from_admin(self, attr, key=None):
        ...

    def _get_from_indexedfield(self, attr, key=None):
        ...

    def get_boost_value(self, boost_key):
        """
        Get the most specifically-defined boost value for the given key
        """
        attr = "boost_parts"
        # # Check if set in ENV
        # try:
        #     setting_value = self._get_from_env(attr, boost_key)
        # except SettingNotFound:

        # Check if present in user settings
        try:
            setting_value = self._get_from_django_settings(attr, boost_key)
        except SettingNotFound:
            # Check if present in defaults
            try:
                setting_value = self._get_from_defaults(attr, boost_key)
            except SettingNotFound:
                setting_value = 1.0
        if setting_value is None:
            setting_value = 1.0

        return setting_value


extended_search_settings = SearchExtendedSettings()
