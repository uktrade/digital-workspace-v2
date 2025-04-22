from django.db.models.query import QuerySet

from core.models.tags import Tag
from interactions.models import TagSubscription
from user.models import User


def subscribe(*, tag: Tag, user: User) -> TagSubscription:
    tag_subscription, _ = TagSubscription.objects.get_or_create(user=user, tag=tag)
    return tag_subscription


def unsubscribe(*, tag: Tag, user: User) -> None:
    TagSubscription.objects.filter(user=user, tag=tag).delete()


def get_subscribed_tags(*, user: User) -> QuerySet[Tag]:
    return Tag.objects.filter(interactions_tagsubscriptions__user=user)
