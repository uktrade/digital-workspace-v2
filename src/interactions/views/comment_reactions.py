from django.http import (
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from interactions.models import ReactionType
from interactions.services import comment_reactions as comment_reactions_service
from news.models import Comment


def react_to_comment(request: HttpRequest, *, pk):
    comment = get_object_or_404(Comment, id=pk)
    user = request.user

    if request.method == "POST":
        reaction_type = ReactionType(request.POST["reaction_type"])
        is_selected = request.POST.get("is_selected") == "true"

        reacted_type = None if is_selected else reaction_type
        comment_reactions_service.react_to_comment(user, comment, reacted_type)

    return JsonResponse(
        {
            "user_reaction": comment_reactions_service.get_user_comment_reaction(
                user, comment
            ),
            "reactions": comment_reactions_service.get_comment_reaction_counts(comment),
        }
    )


@require_http_methods(["GET"])
def get_comment_reaction_users(request: HttpRequest, *, pk):
    comment = get_object_or_404(Comment, id=pk)
    comment_reactions = comment_reactions_service.get_comment_reactions(comment)

    reactions = {}

    for comment_reaction in comment_reactions:
        reaction_type = comment_reaction.type
        user = comment_reaction.user
        reactions.setdefault(reaction_type, []).append(user.get_full_name())

    return JsonResponse({"reactions": reactions})
