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
from waffle import flag_is_active
from wagtail.models import Page

from core import flags
from interactions.models import ReactionType
from interactions.services import bookmarks as bookmarks_service
from interactions.services import comment_reactions as comment_reactions_service
from interactions.services import comments as comments_service
from interactions.services import page_reactions as page_reactions_service
from news.forms import CommentForm
from news.models import Comment


@require_http_methods(["POST"])
def bookmark(request):
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
def remove_bookmark(request, *, pk):
    bookmarks_service.remove_bookmark(pk, request.user)
    return HttpResponse()


@require_http_methods(["GET"])
def bookmark_index(request):
    return TemplateResponse(
        request,
        "interactions/bookmark_index.html",
        context={
            "bookmarks": bookmarks_service.get_bookmarks(request.user),
        },
    )


@require_http_methods(["POST"])
def react_to_page(request, *, pk):
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
def edit_comment(request, *, comment_id):
    if not comments_service.can_edit_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment_message = request.POST.get("comment")
    try:
        comments_service.edit_comment(comment_id, comment_message)
    except comments_service.CommentNotFound:
        raise Http404

    return redirect(
        reverse("interactions:get-comment", kwargs={"comment_id": comment_id})
    )


@require_http_methods(["GET"])
def get_page_comments(request, *, pk):
    page = get_object_or_404(Page, id=pk).specific
    comments = [
        comments_service.comment_to_dict(page_comment)
        for page_comment in comments_service.get_page_comments(page)
    ]

    return TemplateResponse(
        request,
        "dwds/components/comments.html",
        context={
            "user": request.user,
            "comment_count": comments_service.get_page_comment_count(page),
            "comments": comments,
            "comment_form": CommentForm(),
            "comment_form_url": reverse("interactions:comment-on-page", args=[pk]),
            "request": request,
        },
    )


@require_http_methods(["GET"])
def get_comment(request, *, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment_dict = comments_service.comment_to_dict(comment)

    show_reply_form = request.GET.get("show_reply_form", False)

    return TemplateResponse(
        request,
        "dwds/components/comment.html",
        context={
            "comment": comment_dict,
            "request": request,
            "show_reply_form": show_reply_form,
        },
    )


@require_http_methods(["GET"])
def edit_comment_form(request, *, comment_id):
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
def reply_to_comment(request, *, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    comments_service.add_page_comment(
        comment.page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", comment_id),
    )

    return redirect(
        reverse("interactions:get-comment", kwargs={"comment_id": comment_id})
    )


def react_to_comment(request, *, pk):
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
def comment_on_page(request, *, pk):
    page = get_object_or_404(Page, id=pk).specific
    user = request.user

    comment = comments_service.add_page_comment(
        page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", None),
    )

    if not flag_is_active(request, flags.NEW_COMMENTS):
        return redirect(page.url + f"#comment-{comment.id}")

    return redirect(reverse("interactions:get-page-comments", kwargs={"pk": pk}))


@require_http_methods(["POST"])
def hide_comment(request: HttpRequest, pk: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=pk)
    if not comments_service.can_hide_comment(request.user, comment):
        return HttpResponseForbidden()

    comments_service.hide_comment(comment)

    return redirect(
        reverse("interactions:get-page-comments", kwargs={"pk": comment.page.pk})
    )
