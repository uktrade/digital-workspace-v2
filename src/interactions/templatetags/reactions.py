from django import template
from django.urls import reverse

from interactions.models import ReactionType
from interactions.services import reactions as reactions_service


register = template.Library()


@register.inclusion_tag("interactions/reactions.html")
def reactions_list(user, page):
    reactions = reactions_service.get_reaction_counts(page)
    user_reaction = reactions_service.get_user_reaction(user, page)
    post_url = reverse("interactions:reaction")
    return {
        "reactions": reactions,
        "user_reaction": user_reaction,
        "reaction_selected": user_reaction is not None,
        "post_url": post_url,
        "page": page,
    }


@register.simple_tag
def get_reaction_icon_template(reaction_type: ReactionType) -> str:
    ICON_TEMPLATES = {
        ReactionType.CELEBRATE: "dwds/icons/celebrate.html",
        ReactionType.LIKE: "dwds/icons/like.html",
        ReactionType.LOVE: "dwds/icons/love.html",
        ReactionType.DISLIKE: "dwds/icons/dislike.html",
        ReactionType.UNHAPPY: "dwds/icons/unhappy.html",
    }

    return ICON_TEMPLATES[reaction_type]
