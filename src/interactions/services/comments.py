from datetime import datetime

from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from wagtail.models import Page

from interactions.services import comments as comments_service
from news.forms import CommentForm
from news.models import Comment
from user.models import User


class CommentNotFound(Exception): ...


def edit_comment(pk: str, content: str) -> None:
    comment = Comment.objects.get(pk=pk)
    comment.content = content
    comment.edited_date = datetime.now()
    comment.save()


def add_page_comment(
    page: Page, commenter: User, comment: str, in_reply_to: int
) -> Comment:
    return Comment.objects.create(
        content=comment,
        author=commenter,
        page=page,
        parent_id=in_reply_to,
    )


def get_page_comments(page: Page) -> QuerySet[Comment]:
    if hasattr(page, "comments"):
        return page.comments.filter(parent_id=None, is_visible=True).order_by(
            "-posted_date"
        )
    return Comment.objects.none()


def get_page_comment_count(page: Page) -> int:
    if hasattr(page, "comments"):
        return (
            page.comments.filter(is_visible=True)
            .filter(models.Q(parent__isnull=True) | models.Q(parent__is_visible=True))
            .count()
        )
    return 0


def get_comment_replies(comment: Comment) -> QuerySet[Comment]:
    return comment.replies.filter(is_visible=True)


def get_comment_reply_count(comment: Comment) -> int:
    return comment.replies.filter(is_visible=True).count()


def comment_to_dict(comment: Comment) -> dict:
    include_replies = bool(not comment.parent)

    replies: list[dict] = []
    if include_replies:
        for reply in get_comment_replies(comment):
            replies.append(comment_to_dict(reply))

    comment_dict = {
        "id": comment.pk,
        "allow_reactions": comment.page.specific.allow_reactions,
        "posted_date": comment.posted_date,
        "edited_date": comment.edited_date,
        "message": comment.content,
        "show_replies": include_replies,
        "reply_count": get_comment_reply_count(comment),
        "replies": replies,
        "edit_comment_form_url": reverse(
            "interactions:edit-comment-form",
            kwargs={
                "comment_id": comment.pk,
            },
        ),
        "edit_comment_cancel_url": reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.pk,
            },
        ),
        "reply_comment_form_url": (
            reverse(
                "interactions:get-comment",
                kwargs={
                    "comment_id": comment.pk,
                },
            )
            + "?show_reply_form=True"
        ),
        "reply_comment_url": reverse(
            "interactions:reply-comment",
            kwargs={
                "comment_id": comment.pk,
            },
        ),
        "reply_comment_cancel_url": reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.pk,
            },
        ),
    }

    if author_profile := getattr(comment.author, "profile", None):
        comment_dict.update(
            author_name=author_profile.full_name,
            author_url=reverse("profile-view", args=[author_profile.slug]),
            author_image_url=(
                author_profile.photo.url if author_profile.photo else None
            ),
        )
    else:
        comment_dict.update(
            author_name=comment.author.get_full_name(),
        )

    if include_replies:
        comment_dict.update(
            reply_form_url=reverse(
                "interactions:comment-on-page", args=[comment.page.pk]
            ),
        )

    return comment_dict


def show_comment(comment: Comment) -> None:
    comment.is_visible = True
    comment.save(update_fields=["is_visible"])


def hide_comment(comment: Comment) -> None:
    comment.is_visible = False
    comment.save(update_fields=["is_visible"])


def can_hide_comment(user: User, comment: Comment | int) -> bool:
    if isinstance(comment, int):
        comment = Comment.objects.get(id=comment)

    assert isinstance(comment, Comment)
    return user == comment.author


def can_edit_comment(user: User, comment: Comment | int) -> bool:
    if isinstance(comment, int):
        comment = Comment.objects.get(id=comment)

    assert isinstance(comment, Comment)
    return user == comment.author


def can_reply_comment(user: User, comment: Comment | int) -> bool:
    if isinstance(comment, int):
        comment = Comment.objects.get(id=comment)

    assert isinstance(comment, Comment)
    return not bool(comment.parent)


def get_page_comments_response(request: HttpRequest, page: Page) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

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
            "comment_form_url": reverse("interactions:comment-on-page", args=[page.pk]),
            "request": request,
        },
    )


def get_comment_response(request: HttpRequest, comment: Comment | int) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    if isinstance(comment, int):
        comment = get_object_or_404(Comment, id=comment)

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
