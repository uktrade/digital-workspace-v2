from wagtail.models import Page

from interactions.models import Reaction, ReactionType
from news.models import NewsPage
from user.models import User


def manage_reaction(user: User, page: Page, reaction_type: str):

    if not isinstance(page, NewsPage):
        raise ValueError("The page must be a NewsPage.")

    if not reaction_type or reaction_type not in ReactionType.values:
        Reaction.objects.filter(user=user, page=page).delete()
        return None

    return Reaction.objects.update_or_create(
        user=user, page=page, defaults={"type": reaction_type}
    )
