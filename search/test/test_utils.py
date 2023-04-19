import doctest

import search


def test_doctests():
    results = doctest.testmod(search.utils)
    assert results.failed == 0
