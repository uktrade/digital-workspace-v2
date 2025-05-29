from django.db.models import Count
from wagtail.models import Page

from interactions.models import PageReaction, ReactionType
from interactions.services.reactions import get_active_reactions
from news.models import NewsPage
from user.models import User


def react_to_page(
    user: User, page: Page, reaction_type: str | None
) -> PageReaction | None:
    page = page.specific
    if not isinstance(page, NewsPage):
        raise ValueError("The page must be a NewsPage.")

    if reaction_type is None:
        PageReaction.objects.filter(user=user, page=page).delete()
        return None

    if reaction_type not in ReactionType.values:
        raise ValueError(f"{reaction_type} is not a valid reaction type.")

    reaction, created = PageReaction.objects.update_or_create(
        user=user, page=page, defaults={"type": reaction_type}
    )

    return reaction


def get_page_reactions(page: Page) -> dict | None:
    page = page.specific
    if not isinstance(page, NewsPage):
        return None

    return PageReaction.objects.filter(page=page).select_related("user")


def get_page_reaction_count(
    page: Page, reaction_type: ReactionType | None
) -> int | None:
    page = page.specific
    if not isinstance(page, NewsPage):
        return None

    reactions = PageReaction.objects.filter(page=page)

    if reaction_type:
        reactions = reactions.filter(type=reaction_type)

    return reactions.count()


def get_page_reaction_counts(page: Page) -> dict[str, int]:
    page = page.specific
    if not isinstance(page, NewsPage):
        return {}

    reaction_counts = {
        reaction_type: 0
        for reaction_type in ReactionType.values
        if reaction_type in get_active_reactions()
    }

    reactions = (
        PageReaction.objects.filter(page=page)
        .values("type")
        .annotate(count=Count("id"))
    )
    reaction_counts.update(
        {
            reaction["type"]: reaction["count"]
            for reaction in reactions
            if ReactionType(reaction["type"]) in reaction_counts
        }
    )
    return reaction_counts


def get_user_page_reaction(user: User, page: Page) -> ReactionType | None:
    reaction = PageReaction.objects.filter(user=user, page=page).first()
    if reaction:
        return reaction.type
    return None


def has_user_reacted_to_page(user: User, page: Page) -> bool:
    return PageReaction.objects.filter(user=user, page=page).exists()
