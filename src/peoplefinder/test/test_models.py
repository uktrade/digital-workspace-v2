import doctest

import peoplefinder.models


def test_doctests(db):
    results = doctest.testmod(peoplefinder.models)
    assert results.failed == 0


def test_person_field_count():
    assert len(peoplefinder.models.Person._meta.get_fields()) == 62, (
        "It looks like you have updated the `Person` model. Please make sure you have"
        " updated `PersonAuditLogSerializer.serialize` to reflect any field changes."
    )


def test_team_field_count():
    assert len(peoplefinder.models.Team._meta.get_fields()) == 16, (
        "It looks like you have updated the `Team` model. Please make sure you have"
        " updated `TeamAuditLogSerializer.serialize` to reflect any field changes."
    )
