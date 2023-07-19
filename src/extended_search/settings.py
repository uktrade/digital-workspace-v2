from collections import ChainMap
from collections.abc import Mapping
import environ

from django.conf import settings as django_settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

from extended_search.index import RelatedFields
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
            if value := self._getitem_overriding_maps(key):
                return value
            return self.__missing__(key)

        if isinstance(submaps[0][key], Mapping):
            # Return an instance of this class, ChainMapping sub-dicts
            cls = self.__class__
            return cls(
                *(submap[key] for submap in submaps),
                prefix=self._get_prefixed_key_name(key, self.prefix),
            )

        if value := self._getitem_overriding_maps(key):
            return value

        return super().__getitem__(key)

    def __missing__(self, key):
        # Check if we're using a flat key that wasn't overridden from the dicts
        if key in self.all_keys:
            return self._getitem_from_maps_for_prefixed_key(key, self)
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

    @property
    def all_keys(self):
        """
        Returns a list of the *flattened* keys for all nested maps in this instance
        """
        return self._get_all_prefixed_keys_from_nested_maps(self, "")

    def _getitem_from_maps_for_prefixed_key(self, key, dict):
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

        return self._getitem_from_maps_for_prefixed_key(
            self.nesting_separator.join(key_elements), dict[sub_key]
        )

    def _getitem_overriding_maps(self, key):
        """
        Placeholder for implementing non-dict overrides of specfic keys - i.e.
        if we want to be able to have a method that supports overriding a deep
        single key we don't need to artificially create a deep nested dict and
        add it to the ChainMap, we can support it here instead...
        """
        return None


class Settings(NestedChainMap):
    """
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

    def __init__(self, *args, **kwargs):
        if "prefix" in kwargs and kwargs["prefix"] is not None:
            # This instance is a sub-map used for the recursive / nested structure
            return super().__init__(*args, **kwargs)

        self.defaults = DEFAULT_SETTINGS
        self.django_settings = getattr(django_settings, SETTINGS_KEY, {})
        return super().__init__(self.django_settings, self.defaults)

    def __missing__(self, key):
        # if it's a field key we search specifically for it, or default to 1.0
        original_key = key
        if f"{self.nesting_separator}fields" in key:
            key = key.split(self.nesting_separator)[-1:][0]

        if value := self._get_value_from_field_definition(key):
            return value

        return super().__missing__(original_key)

    def _get_value_from_db(self, key):
        try:
            setting = Setting.objects.get(
                key=self._get_prefixed_key_name(key, self.prefix)
            )
            return setting.value
        except Setting.DoesNotExist:
            return None

    def _get_value_from_env(self, key):
        try:
            # Check for a leaf-level key
            return env(
                f"{SETTINGS_KEY}{self.nesting_separator}{self._get_prefixed_key_name(key, self.prefix)}"
            )
        except ImproperlyConfigured:
            try:
                # check for a full string concatenated key
                return env(f"{SETTINGS_KEY}{self.nesting_separator}{key}")
            except ImproperlyConfigured:
                ...

    def _get_value_from_field_definition(self, key):
        """
        Requires the key to be in the format `app_name.model_class.field_name`
        """
        key_elements = key.split(".")
        # fields can have a dot-notation name if RelatedFields
        if len(key_elements) >= 3:
            app_name, model_class, *field_name_parts = key_elements
            field_name = ".".join(field_name_parts)
            try:
                content_type = ContentType.objects.get_by_natural_key(
                    app_name, model_class
                )
            except ContentType.DoesNotExist:
                # Not a validly defined field key
                return None
            model = content_type.model_class()
            fields = getattr(model, "search_fields", [])
            for field in fields:
                if (
                    isinstance(field, RelatedFields)
                    and field.model_field_name == field_name_parts[0]
                ):
                    for related_field in field.fields:
                        if boost := self._get_boost_value_if_matching_field(
                            field_name_parts[1], related_field
                        ):
                            return boost
                else:
                    if boost := self._get_boost_value_if_matching_field(
                        field_name, field
                    ):
                        return boost

    def _get_boost_value_if_matching_field(self, field_name_key, field):
        try:
            field_name = field.model_field_name
        except AttributeError:
            field_name = field.field_name

        if field_name_key == field_name:
            return getattr(field, "boost", 1.0)

    def _getitem_overriding_maps(self, key):
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


extended_search_settings = Settings()
