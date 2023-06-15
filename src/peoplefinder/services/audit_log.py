from abc import ABC, abstractmethod
from typing import Literal, Optional, Type, TypedDict, Union

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet

from peoplefinder.models import AuditLog
from user.models import User


ObjectReprKey = str
# Note that we do not support using a dict as a value.
ObjectReprValue = Union[None, bool, str, int, float, list]
ObjectRepr = dict[ObjectReprKey, ObjectReprValue]

# It's best to never change these values. If you do ever change them, then all previous
# audit log diffs will need to be updated.
DiffAction = Literal["add", "change", "remove"]


class DiffItem(TypedDict):
    action: DiffAction
    key: ObjectReprKey
    from_value: ObjectReprValue
    to_value: ObjectReprValue


Diff = list[DiffItem]


class AuditLogSerializer(ABC):
    """An abstract base class for serializing a model that requires an audit log."""

    SERIALIZERS: dict[models.Model, Type["AuditLogSerializer"]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        cls.SERIALIZERS[cls.model] = cls

    @property
    @abstractmethod
    def model(self) -> models.Model:
        """Return the model related to this serializer."""
        raise NotImplementedError

    @abstractmethod
    def serialize(self, instance: models.Model) -> ObjectRepr:
        """Serialize and return an object repr of the model instance.

        Important notes:
            * The result must map cleanly to JSON without any required encoding.
                * Do NOT return `datetime` even if they will be encoded. Convert it to a
                  `str` before returning.
                * Same for fields like `UUID`. They must be encoded to a `str` here.
                * The output from this function will be diffed against the JSON object
                  from the previous audit log so follow the rules carefully.
            * Do NOT return a `dict` for a value. The object repr should be "flat".
            * Look at `ObjectReprValue` to check what is a valid value.
            * Denormalize relationships to other models. Here are some examples:
                * Use `list` to represent one-to-many relationships.
                * Use `ArrayAgg` for many-to-many relationships.
            * Check out `PersonAuditLogSerializer` as an example.

        Args:
            instance: The instance to be serialized.

        Returns:
            The object repr of the instance.
        """
        raise NotImplementedError


class AuditLogService:
    @classmethod
    def log(
        cls, action: AuditLog.Action, actor: Optional[User], instance: models.Model
    ) -> AuditLog:
        """Insert a log of changes made to the given instance.

        Args:
            action: What action was performed.
            actor: Who performed the action.
            instance: What model was changed.

        Returns:
            The related audit log record.
        """
        serializer = AuditLogSerializer.SERIALIZERS[type(instance)]

        try:
            prev = cls.get_audit_log(instance).latest()
        except AuditLog.DoesNotExist:
            prev = None

        object_repr: ObjectRepr
        diff: Diff

        if action == AuditLog.Action.CREATE:
            object_repr = serializer().serialize(instance)
            diff = []
        elif action == AuditLog.Action.DELETE:
            object_repr = {}
            diff = []
        elif action == AuditLog.Action.UPDATE:
            object_repr = serializer().serialize(instance)
            diff = object_repr_diff(prev.object_repr if prev else {}, object_repr)
        else:
            raise ValueError("Unknown audit log action")

        return AuditLog.objects.create(
            content_object=instance,
            actor=actor,
            action=action,
            object_repr=object_repr,
            diff=diff,
        )

    @staticmethod
    def get_audit_log(instance: models.Model) -> QuerySet:
        return AuditLog.objects.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
        )


def object_repr_diff(old: ObjectRepr, new: ObjectRepr) -> Diff:
    """Return the difference between the old and new object reprs.

    Note that this function only performs a superficial diff.

    This function will only diff the top level of the objects and performs a simple `!=`
    check to see if the values differ. This means that if it comes across 2 lists tha  are not the same, it will simply output that the whole value has changed.

    These limitations are not an issue for the purpose of generating audit log diffs.

    Args:
        old: The old object repr.
        new: The new object repr.

    Returns:
        The differences between the 2 object reprs.
    """
    diff: Diff = []

    old_keys = set(old)
    new_keys = set(new)

    removed_keys = old_keys - new_keys
    common_keys = old_keys & new_keys
    added_keys = new_keys - old_keys

    for key in removed_keys:
        diff.append(
            {"action": "remove", "key": key, "from_value": old[key], "to_value": None}
        )
    for key in common_keys:
        if old[key] != new[key]:
            diff.append(
                {
                    "action": "change",
                    "key": key,
                    "from_value": old[key],
                    "to_value": new[key],
                }
            )
    for key in added_keys:
        diff.append(
            {"action": "add", "key": key, "from_value": new[key], "to_value": None}
        )

    return diff
