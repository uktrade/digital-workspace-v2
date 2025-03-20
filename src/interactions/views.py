from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from interactions.models import ReactionType
from interactions.services import bookmarks as bookmarks_service
from interactions.services import comment_reactions as comment_reactions_service
from interactions.services import comments as comments_service
from interactions.services import page_reactions as page_reactions_service
from news.forms import CommentForm
from news.models import Comment


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
        page_reactions_service.react_to_page(user, page, reacted_type)

    return JsonResponse(
        {
            "user_reaction": page_reactions_service.get_user_page_reaction(user, page),
            "reactions": page_reactions_service.get_page_reaction_counts(page),
        }
    )


@require_http_methods(["POST"])
def edit_comment(request, *args, comment_id, **kwargs):
    if not comments_service.can_edit_comment(request["user"], comment_id):
        return HttpResponse(status=403)

    if request.method == "POST":
        comment_message = request.POST.get("comment")
        try:
            comments_service.edit_comment(comment_message, comment_id)
        except comments_service.CommentNotFound:
            raise Http404

        return HttpResponse(comment_message, content_type="text/html")
    return HttpResponse(status=400)


def edit_comment_form(request, *args, comment_id, **kwargs):
    if not comments_service.can_edit_comment(request["user"], comment_id):
        return HttpResponse(status=403)

    comment = comments_service.comment_to_dict(
        get_object_or_404(Comment, id=comment_id)
    )
    comment.update(
        edit_comment_form=CommentForm(initial={"comment": comment["message"]}),
        edit_comment_url=reverse(
            "interactions:edit-comment",
            kwargs={
                "comment_id": comment_id,
            },
        ),
    )

    return TemplateResponse(
        request,
        "interactions/edit_comment_form.html",
        context={
            "comment": comment,
        },
    )


def react_to_comment(request, *args, pk, **kwargs):
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


@require_http_methods(["POST"])
def comment_on_page(request, *args, pk, **kwargs):
    page = get_object_or_404(Page, id=pk).specific
    user = request.user

    if request.method == "POST":
        comments_service.add_page_comment(
            page,
            user,
            request.POST["comment"],
            request.POST.get("in_reply_to", None),
        )

    return redirect(page.url)


@require_http_methods(["POST"])
def hide_comment(request: HttpRequest, pk: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=pk)
    if not comments_service.can_hide_comment(request.user, comment):
        return HttpResponseForbidden()
    comments_service.hide_comment(comment)
    return HttpResponse(status=200)
