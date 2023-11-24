# Extended Search

This component is pulled out from the "search" since it is not opinionated about the site content being indexed.

There are two levels to this - the first is generic extensions to Wagtail's search functionality (e.g. to enable easier overriding and address issues with boosting). The second is an opinionated approach to search indexing and retrieval based on [Github Doc's search](https://github.blog/2023-03-09-how-github-docs-new-search-works/) and outlined in some detail in the [docs](../../docs/search.md).

Eventually some of this would be good to merge upstream, and the rest could/should be extracted to its own PyPI module.

The default settings are very overridable; the prioority order is DB settings > Field config settings > ENV settings > Django conf settings > default settings.

All default settings are below (note that specific fields will default to `1.0` while extras have no default value):

```py
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
    },
}
```

Any of these can be overridden in the Django settings module with a matching dict under the `SEARCH_EXTENDED` key. This dict does not need to contain all values at any level, only the ones being overridden, for example:

```py
SEARCH_EXTENDED = {
    "boost_parts": {
        "extras": {
            "page_tools_phrase_title_explicit": 2.0,
            "page_guidance_phrase_title_explicit": 2.0,
        },
        "query_types": {
            "phrase": 20.5,
        },
    }
}
```

Where a `boost_part` is for a field, that setting can be overridden by the `boost` attribute in the `IndexedField` configuration in the models, for example:

```py
IndexedField("title", boost=5.0),
```

Individual settings can be overridden with ENV variables, using the nested settings dict's keys, concatenated with `__`, for example:

```py
SEARCH_EXTENDED__boost_parts__query_types__phrase=18.7
```

Lastly, the setting can be overridden by a DB setting administered via the admin, for example:

```py
boost_parts__query_types__phrase=23.4
```
