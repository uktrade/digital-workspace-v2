import json
from django import template

from interactions.models import ReactionType
from interactions.services import reactions as reactions_service


register = template.Library()


@register.inclusion_tag("interactions/reactions.html")
def reactions_list(user, page, reaction_block):
    reactions = reactions_service.get_reaction_counts(page)
    user_reaction = reactions_service.get_user_reaction(user, page)

    return {"reactions": reactions, "user_reaction": user_reaction, "reaction_block": reaction_block}


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

# TBC - may not be needed depending on gtm_datalayer_info
@register.simple_tag(takes_context=True)
def get_gtm_reactions(context) -> str:
    if hasattr(context, "page"):
        page = context["page"]
        reactions = reactions_service.get_reaction_counts(page)
        context['gtm_reactions'] = json.dumps(reactions)
    return ""