from django.http import (
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from interactions.models import ReactionType
from interactions.services import page_reactions as page_reactions_service


@require_http_methods(["POST"])
def react_to_page(request: HttpRequest, *, pk):
    page = get_object_or_404(Page, id=pk)
    user = request.user

    if request.method == "POST":
        reaction_type = ReactionType(request.POST["reaction_type"])
        is_selected = request.POST.get("is_selected") == "true"

        reacted_type = None if is_selected else reaction_type
        page_reactions_service.react_to_page(user, page, reacted_type)

    return JsonResponse(
        {
            "user_reaction": page_reactions_service.get_user_page_reaction(user, page),
            "reactions": page_reactions_service.get_page_reaction_counts(page),
        }
    )
