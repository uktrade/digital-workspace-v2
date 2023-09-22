---
hide:
  - navigation
---

# Search

## How search works

Search is handled by [OpenSearch](https://opensearch.org/), an [ElasticSearch](https://www.elastic.co/) clone that runs as a service on AWS. Indexing and querying is managed by an extension to [Wagtail's in-built search](https://docs.wagtail.org/en/stable/topics/search/index.html) functionality.

This document outlines how that process is customised; the original process is based on the setup used by [Github Doc's search](https://github.blog/2023-03-09-how-github-docs-new-search-works/).

This approach balances comprehensiveness (resurn all results) with a nuanced ability to tweak values for searches, so that the most relevant results should be first, and if not it's relatively easy to iteratively improve them.

If you are simply looking for the boost calculations, head straight for the end of this document.

## Indexing

The first step is to control our search indexing in detail. Each searchable object type is listed below, along with the ORM fields that object contains that merit indexing; that is to say any data on that object that users may at any point use to search, refine or filter in order to find the result they are looking for.

### Title, headings, excerpt and content

Each content editable text field on every page and content type (as far as possible) will be combined into only 4 fields (actually 8, see the next section); `title`, `headings`, `excerpt` and `content`. This is to minimise storage and retrieval times for OpenSearch, while separating the content into chunks that may be boosted independently.

Matches on document titles should be more relevant than matches on heading, which are more relevant than matches on the excerpt, which in turn are more relevant than matches within the body content. At the same time matches anywhere within the content should be equally ranked, and (for simplicity) we treat matches in any heading as equally valid.

As an example, a page containing headings "How to sign up" and "Quick start" would be indexed as a document with the `headings` field contents being "How to sign up Quick start".

Note that fields containing metadata for filtering etc will also be present on the search documents.

### Explicit fields

Each text field on each of the models above will be indexed twice; first as a raw, unprocessed field with an `_explicit` suffix, and also as a stemmed and procesed field using the standard field name (this "tokenized" approach is the Wagtail default). Non-text fields will be indexed unprocessed with no suffix.

As an example, a `Page` model with a `title` field would be indexed as a `Page` document in OpenSearch, containing both `title` and `title_explicit` fields. The `title` field will support misspellings and stemmings (see below) while the `title_explicit` field exists in order to be able to prioritise results containing exact matches.

### Stemming

Stemming maps different forms of the same word to a common "stem" - for example, the English stemmer maps *connection*, *connections*, *connective*, *connected*, and *connecting* to *connect*. So a search for *connected* would also find documents which only have the other forms.

We use the standard [Snowball stemmer](https://snowballstem.org/) (English version) as recommended by ElasticSearch, OpenSearch and Wagtail, as well as the Github Docs team. It supports English language synonyms as well as stemming different forms of the same word, and it tries to avoid stemming similar words with different meanings as the same stem (even when they're based on the same root word).

## Retrieval

As we ask OpenSearch to return results (documents) relating to the user's query, we will apply a series of "boost" values to various different configurations of the results. OpenSearch uses these boost values to give each result a score, which is how the results get ranked (note that the score itself doen't matter; what matters is the relative scores of different results).

Rather than send a single query to OpenSearch, we send a set of similar queries which allows us to ask for various types of match, all ranked according to their likelihood to be what the user is looking for.

An example is that we may ask for both and exact match and a fuzzy match for the same term in the same query, with the exact match having a higher score. Each search result will only be included once but this approach maximises the chances of:
 - returning results that match explicit (possibly advanced, complex) queries
 - returning relevant results to broader, less explicit queries

In reality each query submitted by the user will result in at least 7 individual search operations, often 19, and perhaps more depending on filtering etc. These will be managed within a single query to OpenSearch, and turnaround times should not suffer as a result.

Note that this means we have very large DSL strctures representing our search queries to OpenSearch.

### Single or multiple term; AND, OR and Phrase matching

Searching for a single word or term is relatively simple; we want to search against each field and prioritise the fields with more importance, and where we have to use less processing (thereby giving priority to results that are exactly as typed by the user, rather than e.g. word variants).

When searching for terms containing multiple word we want to do all the above, but we also want to combine the words so that by default we search using *both* AND and OR strategies. Results for the AND search will be boosted higher than results for the OR search.

Effectively a search for "paper aeroplane" should return any document containing either word; at the same time it should rank results containing both "paper" and "aeroplane" higher than results with only the word "paper" or the word "aeroplane".

In addition, we also want to use "phrase" searching, where the set of words must all appear together in the same order; this is boosted above AND and OR matches as most relevant, and of course even more so if it's matched against unprocessed (explicit) fields.

### Fuzzy matching

To take account of misspellings, we'll include [fuzzy matching](https://docs.wagtail.org/en/stable/topics/search/searching.html#fuzzy-matching) of terms so that "similar" words will be returned even when they don't exactly match any word or stem.

Fuzzy matching will only be applied to Page titles and key fields on other records, like Person names.

In order that these results are always below any non-fuzzy matches, the boost values for these results will be fractional; when multiplied they will relatively lower the relevancy score of the results returned by this search.

### Filtering

Non-text fields like dates etc will be indexed to support the results being filtered by these values.

### Advanced search terms

This multi-dimensional approach to search, with a complex set of queries representing various different ways to retrieve each given search term, avoids the need for "advanced search" queries being exposed to the user. As such, users will not benefit from trying to use keyword like "AND" or boolean symbols like "-" in their search queries.

### How boosting is applied

As per the latest approach implemented by OpenSearch, no boosting is applied at index time - all boost values are calculated at retrieval time and applied in depth to each query.

TO calculate a query's boost value, the specific boost components for the field type, the analysis type, and the query type (i.e. phrase vs AND vs OR vs fuzzy) are multiplied together. In some cases extra values may be multiplied in to account for e.g. prioritising an exact match of a Tools page over other types.

This calculated value is then applied to a specific query, and this query is merged with the others in the matrix we're applying to create an overall DSL that's sent to OpenSearch. The bossts are applied to the subqueries, resulting in a set of results for which the scores have all been calculated according to the various vboosts applied.

## Document types

OpenSearch treats each potential result as a "document" - it doesn't distinguish between pages, people, tools, news pages, etc. It's therefore important in our combined search that our boost values work together as a whole, with the boosts appropriately scaled.

# Boost values

The following are the various base boost values we use in the search setup. When a search request is constructed, these values are multiplied together as appropriate for each specific type of query we send to OpenSearch.

Please note the intention is that these can be modified in a dedicated part of the admin system; these values are therefore only defaults, and based on the GitHub blog post referenced above.

| Boost variable | Score | Description |
|----------------|-------|-------------|
| BOOST_TITLE | 4.0 | Any match on a title field|
| BOOST_HEADINGS | 3.0 | Any match on a non-title heading field|
| BOOST_CONTENT | 1.0 | Any match wihin the content of the document|
| BOOST_PHRASE | 10.0 | Exact match on an entire search phrase|
| BOOST_AND | 2.5 | AND matches represent stronger links between terms than OR matches, they get this boost|
| BOOST_FUZZY | 0.025 | Fuzzy handles basic misspellings gracefully but these results should be low in the list|
| BOOST_EXPLICIT | 3.5 | No stemming or synonyms used; matches are on unprocessed text|
| BOOST_TOKENIZED | 1.0 | Default; stemming and synonyms used for broader matching|

## Boost combinations

These are basic combinations for a generic page type, to illustrate the process.

| Field | Match Type | Boosts |
|-------|------------|--------|
|`title_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_TITLE |
|`title`| Exact Phrase | BOOST_PHRASE * BOOST_TITLE |
|`title_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_TITLE |
|`title`| AND | BOOST_AND * BOOST_TITLE |
|`title_explicit`| OR | BOOST_EXPLICIT * BOOST_TITLE |
|`title`| OR | BOOST_TITLE |
|`headings_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_HEADINGS |
|`headings`| Exact Phrase | BOOST_PHRASE * BOOST_HEADINGS |
|`headings_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_HEADINGS |
|`headings`| AND | BOOST_AND * BOOST_HEADINGS |
|`headings_explicit`| OR | BOOST_EXPLICIT * BOOST_HEADINGS |
|`headings`| OR | BOOST_HEADINGS |
|`content_explicit`| Exact Phrase | BOOST_EXPLICIT * BOOST_PHRASE * BOOST_CONTENT |
|`content`| Exact Phrase | BOOST_PHRASE * BOOST_CONTENT |
|`content_explicit`| AND | BOOST_EXPLICIT * BOOST_AND * BOOST_CONTENT |
|`content`| AND | BOOST_AND * BOOST_CONTENT |
|`content_explicit`| OR | BOOST_EXPLICIT * BOOST_CONTENT |
|`content`| OR | BOOST_CONTENT |
|`title`| OR / Fuzzy | BOOST_FUZZY |


# Notes

The rest of this document is notes for implementation and not documentation

## Specific content types

~~These content-specific boosts are applied to results in their own types and multiplied with any other boosts already applied.~~

Indexed fields are laid out below ~~along with a mapping to the relevbatn search field~~

- ContentPage (N.B. all pages will inherit from / implement these fields)
  - title
  - body (mapped to "content" and "headings" in search index)
  - live filter
  - slug filter (??)
  - first_published_at filter
  - last_published_at filter
- PageTopic
  - topic
- PageWithTopics (most pages inherit from here)
  - topics
- Network page
- NewsCategory
  - category title
- NewsPage
  - news_categories
- Document (i.e. PDFs etc) ??
- Person
  - full_name
  - email
  - contact_email
  - profile_completness (for ordering)
  - has_photo (for ordering)
  - roles (job_titles)
  - team related field
  - town_city_or_region
  - regional_building
  - international_building
  - ~~location_in_building~~
  - key_skills
  - other_key_skills
  - fluent_languages
  - intermediate_languages
  - learning_interests
  - other_learning_interests
  - networks
  - professions
  - additional_roles
  - other_additional_roles
  - buildings
  - is_active filter
  - country filter
  - grade filter
  - do_not_work_for_ditc filter ???
- Team
  - name
  - abbreviation (can we do this with/without spaces to catch e.g. "UK DSE" vs "UKDSE")
  - people ?
  - description
  - leaders ??
  - job_titles ?
- Topic ???
- Tool (will this be a page?)


### News

- BOOST_RECENCY

### Tools

- BOOST_EXACT

### Teams

### People

# Resolved Questions

- Teams - do we want to index e.g. all the job titles within the team? (Y)
- Teams - do we want to index members' names so searhcing a person also returns their team? (N)
- Can we do anything to help find "teams' main pages" as per a piece of feedback? Not a real thing - it was private (but maybe change private to hidden)
- index people against role and team membership
- Index excerpts with their own boost variable
- We add alt tags (actually figcaptions) to content
- people search maybe actually works ok at the moment

# Open questions

- People indexing probably deserves dedicated treatment re fields, boosting, fuzzy matching etc
- What are all the different categories from an indexing point of view (e.g. is "working at DBT" content distinct from general content in any significant way?)
- Do we index excerpts any differently to content? Slightly higher boosted?
- some sort of self-serve debug (why doesnt something turn up)
- people - boosts on having profile pic and profile completeness
- do we need UI to show the matching field - so when you search people against team name you can see why they match
- News needs to prioritise recency - does all content?
