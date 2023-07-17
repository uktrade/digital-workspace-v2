from collections import ChainMap
from collections.abc import Mapping

from django.conf import settings as django_settings


import environ
from django.core.exceptions import ImproperlyConfigured


env = environ.Env()
env.read_env()


DEFAULT_SETTINGS = {
    "BOOST_VARIABLES": {
        "SEARCH_PHRASE": 10.0,
        "SEARCH_QUERY_AND": 2.5,
        "SEARCH_QUERY_OR": 1.0,
        "ANALYZER_EXPLICIT": 3.5,
        "ANALYZER_TOKENIZED": 1.0,
    },
    "ANALYZERS": {
        "TOKENIZED": {
            "es_analyzer": "snowball",
            "index_fieldname_suffix": None,
            "query_types": [
                "PHRASE",
                "QUERY_AND",
                "QUERY_OR",
            ],
        },
        "EXPLICIT": {
            "es_analyzer": "simple",
            "index_fieldname_suffix": "_explicit",
            "query_types": [
                "PHRASE",
                "QUERY_AND",
                "QUERY_OR",
            ],
        },
        "KEYWORD": {
            "es_analyzer": "no_spaces",
            "index_fieldname_suffix": "_keyword",
            "query_types": ["PHRASE"],
        },
        "PROXIMITY": {  # @TODO think this needs cleanup to work more like Fuzzy - i.e. built into query but analyzed as a FileterField
            "es_analyzer": "keyword",
            "index_fieldname_suffix": None,
        },
    },
}

# def _depth_first_update(target: dict, source: Mapping) -> None:
#     for key, val in source.items():
#         if not isinstance(val, Mapping):
#             target[key] = val
#             continue

#         if key not in target:
#             target[key] = {}
#         _depth_first_update(target[key], val)


# class DeepChainMap(ChainMap):
#     """A recursive subclass of ChainMap"""


#     def to_dict(self) -> dict:
#         d = {}
#         for mapping in reversed(self.maps):
#             _depth_first_update(d, mapping)
#         return d


class SettingNotFound(Exception):
    pass


class Settings(ChainMap):
    """
    Priority order (high to low):
    1. DB settings
    2. Model IndexField definitions
    3. ENV variables
    4. Django settings
    5. Defaults in app
    """

    def __init__(self, *args, **kwargs):
        self.defaults = DEFAULT_SETTINGS
        self.django_settings = self.get_file_settings()
        self.env_settings = self.get_env_settings()
        return super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        submaps = [mapping for mapping in self.maps if key in mapping]
        if not submaps:
            return self.__missing__(key)
        if isinstance(submaps[0][key], Mapping):
            return Settings(*(submap[key] for submap in submaps))
        return super().__getitem__(key)

    def get_file_settings(self):
        return getattr(django_settings, "SEARCH_EXTENDED", {})

    def get_env_settings(self):
        """
        allows dicts in the format defined in https://django-environ.readthedocs.io/en/latest/types.html#environ-env-dict
        e.g. `SEARCH_EXTENDED=key=val,foo=bar`
        """
        ...


# class SearchExtendedSettings:
#     def __getattr__(self, attr):
#         # # Check if set in ENV
#         # try:
#         #     setting_value = self._get_from_env(attr)
#         #     return setting_value
#         # except NotFoundInSettings:

#         # Check if present in user settings
#         try:
#             setting_value = self._get_from_django_settings(attr)
#             return setting_value
#         except NotFoundInSettings:
#             # Check if present in defaults
#             try:
#                 default_value = self._get_from_defaults(attr)
#                 return default_value
#             except NotFoundInSettings:
#                 raise AttributeError(f"No value set for SEARCH_EXTENDED['{attr}']")

#     def _get_from_env(self, attr, key=None):
#         setting_name = "SEARCH_EXTENDED_" + attr
#         try:
#             setting_value = env(setting_name)
#         except ImproperlyConfigured:
#             raise NotFoundInSettings()

#         if key is not None:
#             return getattr(setting_value, key)
#         return setting_value

#     def _get_from_django_settings(self, attr, key=None):
#         django_settings = getattr(settings, "SEARCH_EXTENDED", {})
#         if attr in django_settings:
#             if key is not None:
#                 return getattr(django_settings[attr], key, None)
#             return django_settings[attr]
#         raise NotFoundInSettings()

#     def _get_from_defaults(self, attr, key=None):
#         default_value = DEFAULTS.get(attr, None)
#         if default_value is None:
#             raise NotFoundInSettings()

#         if attr in DEFAULTS:
#             if key is not None:
#                 return getattr(default_value, key, None)
#             return default_value
#         return default_value

#     def _get_from_admin(self, attr, key=None):
#         ...

#     def _get_from_indexedfield(self, attr, key=None):
#         ...

#     def get_boost_value(self, boost_key):
#         """
#         Get the most specifically-defined boost value for the given key
#         """
#         attr = "BOOST_VARIABLES"
#         # # Check if set in ENV
#         # try:
#         #     setting_value = self._get_from_env(attr, boost_key)
#         # except NotFoundInSettings:

#         # Check if present in user settings
#         try:
#             setting_value = self._get_from_django_settings(attr, boost_key)
#         except NotFoundInSettings:
#             # Check if present in defaults
#             try:
#                 setting_value = self._get_from_defaults(attr, boost_key)
#             except NotFoundInSettings:
#                 setting_value = 1.0
#         if setting_value is None:
#             setting_value = 1.0

#         return setting_value


# extended_search_settings = SearchExtendedSettings()
