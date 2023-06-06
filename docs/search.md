# How search works

Search is handled by [OpenSearch](https://opensearch.org/), an [ElasticSearch](https://www.elastic.co/) clone that runs as a service on AWS. Indexing and querying is managed by [Wagtail's in-built search](https://docs.wagtail.org/en/stable/topics/search/index.html) functionality.

This document outlines how that process is customised; the process is based on the setup used by [Github Doc's search](https://github.blog/2023-03-09-how-github-docs-new-search-works/).

If you are simply looking for the boost values, head straight for the end of this document.

## Indexing

The first step is to control our search indexing in detail. Each searchable object type is listed below, along with the ORM fields that object contains that merit indexing; that is to say any data on that object that users may at any point use to search, refine or filter in order to find the result they are looking for.

- BasePage (N.B. all pages will inherit from / implement these fields)
  - Title

### Title, headings, content

Each text field on every page and content type (as far as possible) will be combined into only 3 fields (actually 6, see the next section); `title`, `headings` and `content`. This is to minimise storage and retrieval times for OpenSearch, while separating the content into chunks that may be boosted independently.

Matches on document titles should be more relevant than matches on heading, which are more relevant than matches within the body content. At the same time matches anywhere within the content should be equally ranked, and (for simplicity) we treat matches in any heading as equally valid.

As an example, a page containing headings "How to sign up" and "Quick start" would be indexed as a document with the `headings` field contents being "How to sign up Quick start".

Note that fields containing metadata for filtering etc will also be present on the search documents.

### Explicit fields

Each text field on each of the models above will be indexed twice; first as a raw, unprocessed field with an `_explicit` suffix, and also as a stemmed and procesed field using the standard field name. Non-text fields will be indexed unprocessed with no suffix.

As an example, a `Page` model with a `title` field would be indexed as a `Page` document in OpenSearch, containing both `title` and `title_explicit` fields. The `title` field will support misspellings and stemmings (see below) while the `title_explicit` field will support prioritising results containing exact matches.

### Stemming

Stemming maps different forms of the same word to a common "stem" - for example, the English stemmer maps *connection*, *connections*, *connective*, *connected*, and *connecting* to *connect*. So a search for *connected* would also find documents which only have the other forms.

We use the standard [Snowball stemmer](https://snowballstem.org/) as recommended by ElasticSearch, OpenSearch and Wagtail, as well as the Github Docs team. It supports English language synonyms as well as stemming different forms of the same word, and it tries to avoid stemming similar words with different meanings as the same stem (even when they're based ont he same root word).

## Retrieval

As we ask OpenSearch to return results (documents) relating to the user's query, we will apply a series of "boost" values to various different configurations of the results. OpenSearch uses these boost values to give each result a score, which is how the results get ranked (note that the score itself doen't matter; what matters is the relative scores of different results).

Rather than send a single query to OpenSearch, we send a nested query, which allows us to ask for various types of match, all ranked according to their likelihood to be what the user is looking for.

An example is that we may ask for both and exact match and a fuzzy match for the same term in the same query, with the exact match having a higher score. Each search result will only be included once but this approach maximises the chances of a) returning results that match explicit (possibly advanced, complex) queries, and b) returning relevant results to broader, less explicit queries.

### Single or multiple term

### Fuzzy matching

### AND and OR

### Filtering

### Advanced search terms

## Document types

### All pages

### News pages

### Tools

## Field types

### Title / headings / contents / data

# Boost values

The following are the various base boost values we use in the search setup. When a search request is constructed, these values are multiplied together as appropriate for each specific type of query we send to OpenSearch.

- BOOST_TITLE: 4.0  # Any match on a title field
- BOOST_HEADINGS: 3.0  # Any match on a non-title heading field
- BOOST_CONTENT: 1.0  # Any match wihin the content of the document
- BOOST_PHRASE: 10.0  # Exact match on an entire search phrase
- BOOST_AND: 2.5  # AND matches represent stronger links between terms than OR matches, they get this boost
- BOOST_EXPLICIT: 3.5  # No stemming or synonyms used; matches are on unprocessed text
- BOOST_FUZZY: 0.025  # Fuzzy handles basic misspellings gracefully but these results should be low in the list

## Specific content types

These content-specific boosts are applied to results in their own types and multiplied with any other boosts already applied. To

### News

- BOOST_RECENCY

### Tools

- BOOST_EXACT

## Boost combinations

| Field | Match Type | Boosts |
|-------|------------|--------|
|`title_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_TITLE|
|`title`| Exact Phrase | BOOST_PHRASE * BOOST_TITLE|
|`title_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_TITLE|
|`title`| AND | BOOST_AND * BOOST_TITLE|
|`title_explicit`| OR | BOOST_EXPLICIT * BOOST_TITLE|
|`title`| OR | BOOST_TITLE|
|`headings_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_HEADINGS|
|`headings`| Exact Phrase | BOOST_PHRASE * BOOST_HEADINGS|
|`headings_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_HEADINGS|
|`headings`| AND | BOOST_AND * BOOST_HEADINGS|
|`headings_explicit`| OR | BOOST_EXPLICIT * BOOST_HEADINGS|
|`headings`| OR | BOOST_HEADINGS|
|`content_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_CONTENT|
|`content`| Exact Phrase | BOOST_PHRASE * BOOST_CONTENT|
|`content_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_CONTENT|
|`content`| AND | BOOST_AND * BOOST_CONTENT|
|`content_explicit`| OR | BOOST_EXPLICIT * BOOST_CONTENT|
|`content`| OR | BOOST_CONTENT|
|`title`| OR | BOOST_FUZZY|
