import os
from collections import ChainMap
from collections.abc import Mapping

import environ
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import ProgrammingError
from django.utils.functional import cached_property
from psycopg2.errors import UndefinedTable
from wagtail.search import index

from extended_search import models
from extended_search.index import (
    RelatedFields,
    get_indexed_models,
    SearchField,
    BaseField,
)

env_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env",
)
env = environ.Env()
env.read_env(env_file_path)


SETTINGS_KEY = "SEARCH_EXTENDED"
NESTING_SEPARATOR = "__"
DEFAULT_SETTINGS = {
    "boost_parts": {
        "query_types": {
            "phrase": 10.0,
            "query_and": 2.5,
            "query_or": 1.0,
            "fuzzy": 0.8,
        },
        "analyzers": {
            "explicit": 3.5,
            "tokenized": 1.0,
        },
        "fields": {
            # In the format appname.modelclass.indexedfieldname
            # e.g. "core.basepage.title_explicit": 5.0
        },
        "extras": {
            # Useful when wanting to add specific overrides to queries
        },
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


class NestedChainMap(ChainMap):
    """
    Allows nested ChainMap functionality, with additional flat-key access
    Approach taken from https://github.com/neutrinoceros/deep_chainmap

    As well as accessing nested dictionaries like dict[key][sub_key], it's also
    possible to access like dict[key__sub_key].
    """

    ...

    def __init__(self, *args, prefix=None, nesting_separator=None, **kwargs):
        self.prefix = prefix
        self.nesting_separator = nesting_separator or NESTING_SEPARATOR
        return super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        """
        Handles nested Chainmap functionality
        """
        submaps = [mapping for mapping in self.maps if key in mapping]
        # No matching dict found for key
        if not submaps:
            return self.__missing__(key)

        if isinstance(submaps[0][key], Mapping):
            # Return an instance of this class, ChainMapping sub-dicts
            cls = self.__class__
            return cls(
                *(submap[key] for submap in submaps),
                prefix=self._get_prefixed_key_name(key, self.prefix),
            )

        return super().__getitem__(key)

    def __missing__(self, key):
        # Check if we're using a flat key that wasn't overridden from the dicts
        if key in self.all_keys:
            return self._getitem_from_nested_maps_for_prefixed_key(key, self)
        return super().__missing__(key)

    def _get_prefixed_key_name(self, key, prefix):
        """
        Consistent method for naming leaf-node keys using `__` to separate dict
        levels from the main settings, useful for ENV settings e.g.
        "SEARCH_EXTENDED": {
            "boost_parts":{
                "phrase": 2.5
            }
        }
        -->
        SEARCH_EXTENDED__boost_parts__phrase=2.5
        """
        return f"{prefix}{self.nesting_separator}{key}" if prefix else key

    def _get_all_prefixed_keys_from_nested_maps(self, dict, prefix):
        """
        Returns a list of flattened keys for each key in the nested dict-like
        objects it's passed
        """
        keys = []
        for key in dict.keys():
            key_str = self._get_prefixed_key_name(key, prefix)
            if isinstance(dict[key], Mapping):
                keys += self._get_all_prefixed_keys_from_nested_maps(dict[key], key_str)
            else:
                keys += [
                    key_str,
                ]
        return keys

    # @TODO: just added the cached_property without too much testing
    @cached_property
    def all_keys(self):
        """
        Returns a list of the *flattened* keys for all nested maps in this instance
        """
        return self._get_all_prefixed_keys_from_nested_maps(self, "")

    def _getitem_from_nested_maps_for_prefixed_key(self, key, dict):
        """
        Splits a flattened / prefixed key into parts, and uses those to traverse
        the dict-like ChainMap of settings. Functions as a flattened __getitem__
        for nested objects
        """
        key_elements = key.split(self.nesting_separator)
        if len(key_elements) == 1:
            return dict[key]

        sub_key = key_elements.pop(0)
        if sub_key not in dict:
            raise KeyError(key)

        return self._getitem_from_nested_maps_for_prefixed_key(
            self.nesting_separator.join(key_elements), dict[sub_key]
        )


class SearchSettings(NestedChainMap):
    """
    SearchSettings are returned in priority order (high to low):

    --[Individual settings]--
    1. DB settings
    2. ENV variables
    3. Model IndexField definitions
    --[Whole or part dict settings]--
    4. Django settings
    5. Defaults in app

    Note that settings in the DB, IndexField and ENV are set one by one, while
    those in the Django SearchSettings and the defaults are created as (either full
    or partial/sparse) dicts.
    """

    def __init__(self, *args, **kwargs):
        if "prefix" in kwargs and kwargs["prefix"] is not None:
            # This instance is a sub-map used for the recursive / nested structure
            return super().__init__(*args, **kwargs)

        self.defaults = DEFAULT_SETTINGS
        self.django_settings = getattr(django_settings, SETTINGS_KEY, {})
        # fields, db and env_vars will be properly initialised by AppConfig.ready()
        self.fields = {"boost_parts": {"fields": {}}}
        self.env_vars = {}
        self.db_vars = {}
        self.queryset = models.Setting.objects.all()

        super().__init__(
            self.db_vars,
            self.env_vars,
            self.fields,
            self.django_settings,
            self.defaults,
        )

    def _get_all_indexed_fields(self):
        fields = {}
        for model_cls in get_indexed_models():
            for search_field in model_cls.get_search_fields():
                if isinstance(search_field, SearchField) or isinstance(
                    search_field, RelatedFields
                ):
                    definition_cls = search_field.get_definition_model(model_cls)
                    if definition_cls not in fields:
                        fields[definition_cls] = set()

                    if isinstance(search_field, RelatedFields):
                        for ff in search_field.fields:
                            # ff.is_relation_of(search_field) @TODO check this
                            fields[definition_cls].add(ff)
                    else:
                        fields[definition_cls].add(search_field)

        return fields

    def initialise_field_dict(self):
        # preserve same linked obj while re-initialising it
        self.fields["boost_parts"]["fields"].clear()
        field_dict = self._get_all_indexed_fields()
        for model, fields in field_dict.items():
            model_name_str = f"{model._meta.app_label}.{model._meta.model_name}"
            for search_field in fields:
                if isinstance(search_field, BaseField):
                    field_name_str = search_field.get_full_model_field_name()
                else:
                    field_name_str = search_field.field_name
                field_key = f"{model_name_str}.{field_name_str}"

                self.fields["boost_parts"]["fields"][field_key] = getattr(
                    search_field, "boost", 1.0
                )

    def initialise_env_dict(self):
        # preserve same linked obj while re-initialising it
        self.env_vars.clear()
        for key in self.all_keys:
            try:
                # check for a full string concatenated key
                value = env(f"{SETTINGS_KEY}{self.nesting_separator}{key}")

                if value:
                    key_elements = key.split(self.nesting_separator)
                    sub_dict = self.env_vars
                    for key in key_elements:
                        if key != key_elements[len(key_elements) - 1]:
                            if key not in sub_dict:
                                sub_dict[key] = {}
                            sub_dict = sub_dict[key]
                        else:
                            sub_dict[key] = value
            except ImproperlyConfigured:
                ...

    def initialise_db_dict(self):
        try:
            # preserve same linked obj while re-initialising it
            self.db_vars.clear()
            self.queryset = models.Setting.objects.all()
            for obj in self.queryset:
                key_elements = obj.key.split(self.nesting_separator)
                sub_dict = self.db_vars
                for key in key_elements:
                    if key != key_elements[len(key_elements) - 1]:
                        if key not in sub_dict:
                            sub_dict[key] = {}
                        sub_dict = sub_dict[key]
                    else:
                        sub_dict[key] = obj.value
        except (UndefinedTable, ProgrammingError):
            ...


extended_search_settings = SearchSettings()
