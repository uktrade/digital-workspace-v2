import environ
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

#
# DEFUNCT ALREADY
# This whole file and approach is going to be torn down and re-implemented from
# the ground up in the next PR
#

env = environ.Env()
env.read_env()

DEFAULTS = {
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


class NotFoundInSettings(Exception):
    pass


class SearchExtendedSettings:
    def __getattr__(self, attr):
        # # Check if set in ENV
        # try:
        #     setting_value = self._get_from_env(attr)
        #     return setting_value
        # except NotFoundInSettings:

        # Check if present in user settings
        try:
            setting_value = self._get_from_django_settings(attr)
            return setting_value
        except NotFoundInSettings:
            # Check if present in defaults
            try:
                default_value = self._get_from_defaults(attr)
                return default_value
            except NotFoundInSettings:
                raise AttributeError(f"No value set for SEARCH_EXTENDED['{attr}']")

    def _get_from_env(self, attr, key=None):
        setting_name = "SEARCH_EXTENDED_" + attr
        try:
            setting_value = env(setting_name)
        except ImproperlyConfigured:
            raise NotFoundInSettings()

        if key is not None:
            return getattr(setting_value, key)
        return setting_value

    def _get_from_django_settings(self, attr, key=None):
        django_settings = getattr(settings, "SEARCH_EXTENDED", {})
        if attr in django_settings:
            if key is not None:
                return getattr(django_settings[attr], key, None)
            return django_settings[attr]
        raise NotFoundInSettings()

    def _get_from_defaults(self, attr, key=None):
        default_value = DEFAULTS.get(attr, None)
        if default_value is None:
            raise NotFoundInSettings()

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
        attr = "BOOST_VARIABLES"
        # # Check if set in ENV
        # try:
        #     setting_value = self._get_from_env(attr, boost_key)
        # except NotFoundInSettings:

        # Check if present in user settings
        try:
            setting_value = self._get_from_django_settings(attr, boost_key)
        except NotFoundInSettings:
            # Check if present in defaults
            try:
                setting_value = self._get_from_defaults(attr, boost_key)
            except NotFoundInSettings:
                setting_value = 1.0
        if setting_value is None:
            setting_value = 1.0

        return setting_value


extended_search_settings = SearchExtendedSettings()