from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from interactions.models import ReactionType
from interactions.services import bookmarks as bookmarks_service
from interactions.services import reactions as reactions_service


@require_http_methods(["POST"])
def bookmark(request, *args, **kwargs):
    user = request.user

    if request.method == "POST":
        page_id = int(request.POST["page_id"])
        page = get_object_or_404(Page, id=page_id)

        bookmarks_service.toggle_bookmark(user, page)

        is_bookmarked = bookmarks_service.is_page_bookmarked(user, page)

        context = {
            "post_url": reverse("interactions:bookmark"),
            "user": user,
            "page": page,
            "is_bookmarked": is_bookmarked,
        }

        return TemplateResponse(
            request,
            "interactions/bookmark_page_input.html",
            context,
        )


@require_http_methods(["DELETE"])
def remove_bookmark(request, pk, *args, **kwargs):
    bookmarks_service.remove_bookmark(pk, request.user)
    return HttpResponse()


@require_http_methods(["GET"])
def bookmark_index(request, *args, **kwargs):
    return TemplateResponse(
        request,
        "interactions/bookmark_index.html",
        context={
            "bookmarks": bookmarks_service.get_bookmarks(request.user),
        },
    )


@require_http_methods(["POST"])
def react_to_page(request, *args, pk, **kwargs):
    page = get_object_or_404(Page, id=pk)
    user = request.user

    if request.method == "POST":
        reaction_type = ReactionType(request.POST["reaction_type"])
        is_selected = request.POST.get("is_selected") == "true"

        reacted_type = None if is_selected else reaction_type
        reactions_service.react_to_page(user, page, reacted_type)

    return JsonResponse(
        {
            "user_reaction": reactions_service.get_user_reaction(user, page),
            "reactions": reactions_service.get_reaction_counts(page),
        }
    )
