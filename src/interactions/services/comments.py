from datetime import datetime

from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from wagtail.models import Page

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

    author_profile = comment.author.profile

    replies: list[dict] = []
    if include_replies:
        for reply in get_comment_replies(comment):
            replies.append(comment_to_dict(reply))

    in_reply_to = comment.pk

    comment_dict = {
        "id": comment.id,
        "author_name": author_profile.full_name,
        "author_url": reverse("profile-view", args=[author_profile.slug]),
        "author_image_url": (
            author_profile.photo.url if author_profile.photo else None
        ),
        "posted_date": comment.posted_date,
        "edited_date": comment.edited_date,
        "message": comment.content,
        "show_replies": include_replies,
        "reply_count": get_comment_reply_count(comment),
        "replies": replies,
        "in_reply_to": in_reply_to,
        "edit_comment_form_url": reverse(
            "interactions:edit-comment-form",
            kwargs={
                "comment_id": comment.id,
            },
        ),
        "edit_comment_cancel_url": reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.id,
            },
        ),
        "reply_comment_form": CommentForm(
            initial={"in_reply_to": comment.id},
            auto_id="reply_%s",
        ),
        "reply_comment_form_url": reverse(
            "interactions:reply-comment-form",
            kwargs={
                "comment_id": comment.id,
                "show_reply_form": True,
            },
        ),
        "reply_comment_url": reverse(
            "interactions:reply-comment",
            kwargs={
                "comment_id": comment.id,
            },
        ),
        "reply_comment_cancel_url": reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.id,
            },
        ),
    }

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
    return user == comment.author


def can_edit_comment(user: User, comment: Comment | int) -> bool:
    if isinstance(comment, int):
        comment = Comment.objects.get(id=comment)
    return user == comment.author


def can_reply_comment(user: User, comment: Comment | int) -> bool:
    if isinstance(comment, int):
        try:
            comment = Comment.objects.get(id=comment)
        except Comment.DoesNotExist:
            return False

    return bool(not comment.parent)
