from django.db.models import Count
from wagtail.models import Page

from interactions.models import Reaction, ReactionType
from news.models import NewsPage
from user.models import User


def react_to_page(user: User, page: Page, reaction_type: str | None):

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


def get_reaction_count(page: Page):
    if not isinstance(page, NewsPage):
        return None
    return Reaction.objects.filter(page=page).count()


def get_reaction_counts(page: Page):
    if not isinstance(page, NewsPage):
        return {}

    reaction_counts = {reaction_type: 0 for reaction_type in ReactionType.values}

    reactions = (
        Reaction.objects.filter(page=page).values("type").annotate(count=Count("id"))
    )
    reaction_counts.update(
        {reaction["type"]: reaction["count"] for reaction in reactions}
    )
    return reaction_counts
