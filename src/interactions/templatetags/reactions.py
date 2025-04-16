import json

from django import template
from django.urls import reverse
from django.utils.html import mark_safe
from wagtail.models import Page

from interactions.models import ReactionType
from interactions.services import comment_reactions as comment_reactions_service
from interactions.services import page_reactions as page_reactions_service
from news.models import Comment
from user.models import User


register = template.Library()


@register.inclusion_tag("interactions/reactions.html")
def reactions_for_page(user: User, page: Page, reaction_location: str):
    reactions = page_reactions_service.get_page_reaction_counts(page)
    user_reaction = page_reactions_service.get_user_page_reaction(user, page)
    return {
        "reaction_location": reaction_location,
        "reactions": reactions,
        "user_reaction": user_reaction,
        "reaction_selected": user_reaction is not None,
        "get_url": reverse("interactions:page-reactions", kwargs={"pk": page.pk}),
        "post_url": reverse("interactions:page-reactions", kwargs={"pk": page.pk}),
        "reactions_header": "React to this article",
    }


@register.inclusion_tag("interactions/reactions.html")
def reactions_for_comment(user: User, comment_id: int):
    comment = Comment.objects.get(id=comment_id)
    reactions = comment_reactions_service.get_comment_reaction_counts(comment)
    user_reaction = comment_reactions_service.get_user_comment_reaction(user, comment)
    return {
        "reaction_location": "comment",
        "reactions": reactions,
        "user_reaction": user_reaction,
        "reaction_selected": user_reaction is not None,
        "get_url": reverse("interactions:comment-reactions", kwargs={"pk": comment.pk}),
        "post_url": reverse(
            "interactions:comment-reactions", kwargs={"pk": comment.pk}
        ),
        "group_id": f"comment-{ comment.pk }",
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


@register.filter
def reaction_type_display(reaction_type: str) -> str:
    return ReactionType(reaction_type).label


@register.simple_tag(takes_context=True)
def get_gtm_reactions(context) -> str:
    if "page" in context:
        page = context["page"]
        if isinstance(page, Page):
            reactions = page_reactions_service.get_page_reaction_counts(page)
            return mark_safe(json.dumps(reactions))  # noqa S308
    return ""
