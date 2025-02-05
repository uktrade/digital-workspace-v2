from typing import Iterable

from django.conf import settings
from django.db.models import Count
from wagtail.models import Page

from interactions.models import Reaction, ReactionType
from news.models import NewsPage
from user.models import User


def get_active_reactions() -> list[ReactionType]:
    inactive_reaction_types = [
        ReactionType(rt) for rt in settings.INACTIVE_REACTION_TYPES
    ]
    return [rt for rt in ReactionType if rt not in inactive_reaction_types]


def react_to_page(user: User, page: Page, reaction_type: str | None) -> Reaction | None:
    page = page.specific
    if not isinstance(page, NewsPage):
        raise ValueError("The page must be a NewsPage.")

    if reaction_type is None:
        Reaction.objects.filter(user=user, page=page).delete()
        return None

    if reaction_type not in ReactionType.values:
        raise ValueError(f"{reaction_type} is not a valid reaction type.")

    reaction, created = Reaction.objects.update_or_create(
        user=user, page=page, defaults={"type": reaction_type}
    )

    return reaction


def get_reaction_count(page: Page, reaction_type: ReactionType | None) -> int | None:
    page = page.specific
    if not isinstance(page, NewsPage):
        return None

    reactions = Reaction.objects.filter(page=page)

    if reaction_type:
        reactions = reactions.filter(type=reaction_type)

    return reactions.count()


def get_reaction_counts(page: Page) -> dict[str, int]:
    page = page.specific
    if not isinstance(page, NewsPage):
        return {}

    reaction_counts = {reaction_type: 0 for reaction_type in ReactionType.values}

    reactions = (
        Reaction.objects.filter(page=page).values("type").annotate(count=Count("id"))
    )
    reaction_counts.update(
        {
            reaction["type"]: reaction["count"]
            for reaction in reactions
            if ReactionType(reaction["type"]) in get_active_reactions()
        }
    )
    return reaction_counts


def get_user_reaction(user: User, page: Page) -> ReactionType | None:
    reaction = Reaction.objects.filter(user=user, page=page).first()
    if reaction:
        return reaction.type
    return None


def has_user_reacted(user: User, page: Page) -> bool:
    return Reaction.objects.filter(user=user, page=page).exists()
