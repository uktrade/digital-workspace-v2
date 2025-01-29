from django import template

from interactions.models import ReactionType
from interactions.services import reactions as reactions_service


register = template.Library()


@register.inclusion_tag("interactions/reactions.html")
def reactions_list(user, page):

    reactions = reactions_service.get_reaction_counts(page)  # double-check
    user_reaction = reactions_service.get_user_reaction(user, page)

    return {"reactions": reactions, "user_reaction": user_reaction}


@register.simple_tag
def get_reaction_icon_template(reaction_type: ReactionType) -> str:

    ICON_TEMPLATES = {
        ReactionType.CELEBRATE: "dwds/icons/bookmark.html",
        ReactionType.LIKE: "dwds/icons/bookmark.html",
        ReactionType.LOVE: "dwds/icons/bookmark.html",
        ReactionType.DISLIKE: "dwds/icons/bookmark.html",
        ReactionType.UNHAPPY: "dwds/icons/bookmark.html",
    }

    return ICON_TEMPLATES[reaction_type]
