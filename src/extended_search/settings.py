from collections import ChainMap
from collections.abc import Mapping

from django.conf import settings as django_settings

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


class Settings(ChainMap):
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

    def get_file_settings():
        return getattr(django_settings, "SEARCH_EXTENDED", {})

    def get_env_settings():
        """
        allows dicts in the format defined in https://django-environ.readthedocs.io/en/latest/types.html#environ-env-dict
        e.g. `EXTENDED_SETTINGS=key=val,foo=bar`
        """
        ...


# Priority order (high to low):
# 1. DB settings
# 2. Model IndexField definitions
# 3. ENV variables
# 4. Django settings
# 5. Defaults in app
