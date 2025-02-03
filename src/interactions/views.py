from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from waffle import flag_is_active
from wagtail.models import Page

from core import flags
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
            "is_new_sidebar_enabled": flag_is_active(request, flags.NEW_SIDEBAR),
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
def react_to_page(request, *args, **kwargs):
    user = request.user

    if request.method == "POST":
        page_id = int(request.POST["page_id"])
        reaction_type = str(request.POST["reaction_type"])
        is_selected = request.POST.get("is_selected") == "true"
        page = get_object_or_404(Page, id=page_id)
        if is_selected:
            reactions_service.react_to_page(user, page, None)
        else:
            reactions_service.react_to_page(user, page, reaction_type)
        reactions = reactions_service.get_reaction_counts(page)
        reactions_count = reactions.get(reaction_type, 0)
        user_reaction = reactions_service.get_user_reaction(user, page)
        context = {
            "user_reaction": user_reaction,
            "reaction_type": reaction_type,
            "reaction_count": reactions_count or 0,
            "reaction_selected": not is_selected,
            "csrf_token": request.META.get("CSRF_COOKIE", ""),
            "post_url": reverse("interactions:reaction"),
            "page": page,
            "request": request,
            "reactions": reactions,
        }

        return TemplateResponse(
            request,
            "interactions/reactions.html",
            context,
        )
