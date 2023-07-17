# Extended Search

This component is pulled out from the "search" since it is not opinionated about the site content being indexed.

There are two levels to this - the first is generic extensions to Wagtail's search functionality (e.g. to enable easier overriding and address issues with boosting). The second is an opinionated approach to search indexing and retrieval based on [Github Doc's search](https://github.blog/2023-03-09-how-github-docs-new-search-works/) and outlined in some detail in the [docs](../../docs/search.md).

Eventually some of this would be good to merge upstream, and the rest could/should be extracted to its own PyPI module.
