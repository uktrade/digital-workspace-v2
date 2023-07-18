from collections import ChainMap
from collections.abc import Mapping
import environ

from django.conf import settings as django_settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

from extended_search.models import Setting


env = environ.Env()
env.read_env()

SETTINGS_KEY = "SEARCH_EXTENDED"
NESTING_SEPARATOR = "__"
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


class SettingNotFound(Exception):
    pass


class Settings(ChainMap):
    """
    Allows nested ChainMap functionality, with settings-specific overrides
    Approach taken from https://github.com/neutrinoceros/deep_chainmap

    Settings are returned in priority order (high to low):

    --[Individual settings]--
    1. DB settings
    2. ENV variables
    3. Model IndexField definitions
    --[Whole or part dict settings]--
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
        self.django_settings = getattr(django_settings, SETTINGS_KEY, {})
        return super().__init__(self.django_settings, self.defaults)

    def __getitem__(self, key):
        """
        Handles nested Chainmap functionality, and also breaks out the
        leaf-node override method
        """
        submaps = [mapping for mapping in self.maps if key in mapping]
        if not submaps:
            if value := self.get_overridden_single_item(key):
                return value
            return self.__missing__(key)

        if isinstance(submaps[0][key], Mapping):
            return Settings(
                *(submap[key] for submap in submaps), prefix=self._get_prefixed_key(key)
            )

        if value := self.get_overridden_single_item(key):
            return value

        return super().__getitem__(key)

    def __missing__(self, key):
        # Check if we're using a flat key that wasn't overridden from the dicts
        if key in self.all_keys:
            return self._get_dict_value_for_prefixed_key(key, self)
        return super().__missing__(key)

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
            return f"{self.prefix}{NESTING_SEPARATOR}{key}"
        return key

    def _get_dict_value_for_prefixed_key(self, key, dict):
        key_elements = key.split(NESTING_SEPARATOR)
        if len(key_elements) == 1:
            return dict[key]

        sub_key = key_elements.pop(0)
        if sub_key not in dict:
            raise KeyError(key)

        return self._get_dict_value_for_prefixed_key(
            NESTING_SEPARATOR.join(key_elements), dict[sub_key]
        )

    def _get_keys_from_dict(self, dict, prefix):
        keys = []
        for key in dict.keys():
            key_str = f"{prefix}{NESTING_SEPARATOR}{key}" if prefix else key
            if isinstance(dict[key], Mapping):
                keys += self._get_keys_from_dict(dict[key], key_str)
            else:
                keys += [
                    key_str,
                ]
        return keys

    def _get_value_from_db(self, key):
        try:
            setting = Setting.objects.get(key=self._get_prefixed_key(key))
            return setting.value
        except Setting.DoesNotExist:
            return None

    def _get_value_from_env(self, key):
        try:
            # Check for a leaf-level key
            return env(
                f"{SETTINGS_KEY}{NESTING_SEPARATOR}{self._get_prefixed_key(key)}"
            )
        except ImproperlyConfigured:
            try:
                # check for a full string concatenated key
                return env(f"{SETTINGS_KEY}{NESTING_SEPARATOR}{key}")
            except ImproperlyConfigured:
                ...

    def _get_value_from_field_definition(self, key):
        """
        Requires the key to be in the format `app_name.model_class.field_name`
        """
        key_elements = key.split(".")
        if len(key_elements) == 3:
            try:
                content_type = ContentType.objects.get_by_natural_key(
                    key_elements[0], key_elements[1]
                )
            except ContentType.DoesNotExist:
                # Not a validly defined field key
                return None

            model = content_type.model_class()
            try:
                for field in model.search_fields:
                    if field.field_name == key_elements[2]:
                        return getattr(field, "boost", None)
            except AttributeError:
                ...

    def get_overridden_single_item(self, key):
        """
        Allows for settings defined as single items to jump into the overrides,
        either from ENV or from e.g. field definitions
        """
        # get from DB
        if value := self._get_value_from_db(key):
            return value
        # or get from ENV
        if value := self._get_value_from_env(key):
            return value
        # or get from field level (if applicable)
        if value := self._get_value_from_field_definition(key):
            return value

        return None

    @property
    def all_keys(self):
        return self._get_keys_from_dict(self, "")


extended_search_settings = Settings()
