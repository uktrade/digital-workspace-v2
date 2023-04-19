import doctest

import peoplefinder.models


def test_doctests(db):
    results = doctest.testmod(peoplefinder.models)
    assert results.failed == 0
