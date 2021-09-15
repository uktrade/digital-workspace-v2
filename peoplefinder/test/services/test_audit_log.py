import unittest

import pytest

from peoplefinder.models import AuditLog, Person
from peoplefinder.services.audit_log import (
    AuditLogService,
    PersonAuditLogSerializer,
    object_repr_diff,
)


def test_audit_log_service_log(db):
    person = Person.objects.get(user__email="john.smith@example.com")

    person.first_name = "Joe"
    person.last_name = "Doe"
    person.save()

    log = AuditLogService.log(AuditLog.Action.UPDATE, person.user, person)

    assert log.content_object == person
    assert log.actor == person.user
    assert log.action == AuditLog.Action.UPDATE.value
    assert log.object_repr["first_name"] == "Joe"
    assert log.object_repr["last_name"] == "Doe"
    assert {
        "action": "change",
        "key": "first_name",
        "from_value": "John",
        "to_value": "Joe",
    } in log.diff
    assert {
        "action": "change",
        "key": "last_name",
        "from_value": "Smith",
        "to_value": "Doe",
    } in log.diff


def test_person_audit_log_serializer(db):
    person = Person.objects.get(user__email="john.smith@example.com")

    object_repr = PersonAuditLogSerializer().serialize(person)

    assert not any(isinstance(value, dict) for value in object_repr.values()), (
        "You cannot use a dict as a value. Please see the"
        " `AuditLogSerializer.serialize` docstring for help."
    )

    assert object_repr["roles"] == ["Software Engineer in Software"]


@pytest.mark.parametrize(
    "old,new,diff,msg",
    [
        ({}, {}, [], "no items"),
        ({"x": 1}, {"x": 1}, [], "no changes"),
        (
            {},
            {"x": 1},
            [{"action": "add", "key": "x", "from_value": 1, "to_value": None}],
            "add an item",
        ),
        (
            {"x": 1},
            {"x": 2},
            [{"action": "change", "key": "x", "from_value": 1, "to_value": 2}],
            "change an item",
        ),
        (
            {"x": 1},
            {},
            [{"action": "remove", "key": "x", "from_value": 1, "to_value": None}],
            "remove an item",
        ),
        (
            {"x": [1]},
            {"x": [1, 2]},
            [{"action": "change", "key": "x", "from_value": [1], "to_value": [1, 2]}],
            "change a list",
        ),
        (
            {"c": [1, 2], "r": None, "s": 3.14},
            {"a": "42", "c": [1], "s": 3.14},
            [
                {"action": "add", "key": "a", "from_value": "42", "to_value": None},
                {"action": "change", "key": "c", "from_value": [1, 2], "to_value": [1]},
                {"action": "remove", "key": "r", "from_value": None, "to_value": None},
            ],
            "add, remove and change",
        ),
    ],
)
def test_object_repr_diff(old, new, diff, msg):
    unittest.TestCase().assertCountEqual(object_repr_diff(old, new), diff, msg)
