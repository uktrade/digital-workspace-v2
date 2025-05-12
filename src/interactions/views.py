from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
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
def bookmark(request: HttpRequest):
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
def remove_bookmark(request: HttpRequest, *, pk):
    bookmarks_service.remove_bookmark(pk, request.user)
    return HttpResponse()


@require_http_methods(["GET"])
def bookmark_index(request: HttpRequest):
    return TemplateResponse(
        request,
        "interactions/bookmark_index.html",
        context={
            "bookmarks": bookmarks_service.get_bookmarks(request.user),
            "extra_breadcrumbs": [(None, "Your bookmarks")],
        },
    )


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


@require_http_methods(["POST"])
def edit_comment(request: HttpRequest, *, comment_id):
    if not comments_service.can_edit_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment_message = request.POST.get("comment")
    try:
        comments_service.edit_comment(comment_id, comment_message)
    except comments_service.CommentNotFound:
        raise Http404

    return comments_service.get_comment_response(request, comment_id)


@require_http_methods(["GET"])
def get_page_comments(request: HttpRequest, *, pk):
    page = get_object_or_404(Page, id=pk).specific

    return comments_service.get_page_comments_response(request, page)


@require_http_methods(["GET"])
def get_comment(request: HttpRequest, *, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    return comments_service.get_comment_response(request, comment)


@require_http_methods(["GET"])
def edit_comment_form(request: HttpRequest, *, comment_id):
    if not comments_service.can_edit_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment = get_object_or_404(Comment, id=comment_id)
    comment_dict = comments_service.comment_to_dict(comment)

    comment_dict.update(
        edit_comment_form=CommentForm(initial={"comment": comment_dict["message"]}),
        edit_comment_url=reverse(
            "interactions:edit-comment",
            kwargs={
                "comment_id": comment_id,
            },
        ),
        edit_comment_cancel_url=reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment_id,
            },
        ),
    )

    return TemplateResponse(
        request,
        "interactions/edit_comment_form.html",
        context={
            "comment": comment_dict,
        },
    )


@require_http_methods(["POST"])
def reply_to_comment(request: HttpRequest, *, comment_id):
    if not comments_service.can_reply_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    comments_service.add_page_comment(
        comment.page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", comment_id),
    )

    return comments_service.get_comment_response(request, comment)


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


@require_http_methods(["POST"])
def comment_on_page(request: HttpRequest, *, pk):
    page = get_object_or_404(Page, id=pk).specific
    user = request.user

    comments_service.add_page_comment(
        page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", None),
    )

    return comments_service.get_page_comments_response(request, page)


@require_http_methods(["POST"])
def hide_comment(request: HttpRequest, pk: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=pk)
    if not comments_service.can_hide_comment(request.user, comment):
        return HttpResponseForbidden()

    comments_service.hide_comment(comment)

    return comments_service.get_page_comments_response(request, comment.page)
