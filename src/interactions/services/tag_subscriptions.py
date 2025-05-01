from datetime import date, datetime
from typing import Iterable

from django.db.models import Subquery
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.utils import timezone

from content.models import ContentPage
from core.models.tags import Tag, TaggedPage, TaggedPerson, TaggedTeam
from interactions.models import TagSubscription
from user.models import User


def subscribe(*, tag: Tag, user: User) -> TagSubscription:
    tag_subscription, _ = TagSubscription.objects.get_or_create(user=user, tag=tag)
    return tag_subscription


def unsubscribe(*, tag: Tag, user: User) -> None:
    TagSubscription.objects.filter(user=user, tag=tag).delete()


def is_subscribed(*, tag: Tag, user: User) -> bool:
    return TagSubscription.objects.filter(user=user, tag=tag).exists()


def get_subscribed_tags(*, user: User) -> QuerySet[Tag]:
    return Tag.objects.filter(interactions_tagsubscriptions__user=user)


def get_tagged_teams(*, tags: Iterable[Tag]) -> BaseManager[TaggedTeam]:
    return TaggedTeam.objects.select_related("content_object").filter(
        tag__in=tags,
    )


def get_tagged_people(*, tags: Iterable[Tag]) -> BaseManager[TaggedPerson]:
    return TaggedPerson.objects.select_related("content_object").filter(
        tag__in=tags,
    )


def get_tagged_pages(*, tags: Iterable[Tag]) -> BaseManager[TaggedPage]:
    return TaggedPage.objects.select_related("content_object").filter(
        tag__in=tags,
    )


def get_tagged_content(
    *, tags: Iterable[Tag]
) -> tuple[BaseManager[TaggedTeam], BaseManager[TaggedPerson], BaseManager[TaggedPage]]:
    return (
        get_tagged_teams(tags=tags),
        get_tagged_people(tags=tags),
        get_tagged_pages(tags=tags),
    )


def get_activity(
    *,
    tags: Iterable[Tag],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict[date, BaseManager[ContentPage]]:
    batch_content_count = 50
    current_content_count = 0

    if not date_from:
        date_from = timezone.now()
    if not date_to:
        date_to = date_from - timezone.timedelta(days=3)

    tagged_teams, tagged_people, tagged_pages = get_tagged_content(tags=tags)
    # team_ids = tagged_teams.values_list("content_object_id", flat=True)
    # person_ids = tagged_people.values_list("content_object_id", flat=True)

    content_datetime = date_from
    grouped_content: dict[date, BaseManager[ContentPage]] = {}
    while content_datetime >= date_to or current_content_count > batch_content_count:
        content_pages = (
            ContentPage.objects.filter(
                id__in=Subquery(tagged_pages.values("content_object_id")),
                latest_revision_created_at__lte=content_datetime,
                latest_revision_created_at__gt=content_datetime
                - timezone.timedelta(days=1),
            )
            .annotate_with_comment_count()
            .annotate_with_reaction_count()
            .specific()
            .order_by("latest_revision_created_at")
        )
        if content_pages.exists():
            grouped_content[content_datetime.date()] = content_pages
            current_content_count += content_pages.count()
        content_datetime -= timezone.timedelta(days=1)

    return grouped_content
