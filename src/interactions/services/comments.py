from django.db.models import QuerySet
from django.urls import reverse
from wagtail.models import Page

from news.models import Comment
from user.models import User


class CommentNotFound(Exception): ...


def edit_comment(content: str, pk: str) -> None:
    try:
        comment = Comment.objects.get(pk=pk)
    except Comment.DoesNotExist:
        raise CommentNotFound()

    if comment:
        comment.content = content
        comment.save()


def add_page_comment(
    page: Page, commenter: User, comment: str, in_reply_to: int
) -> None:
    Comment.objects.create(
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
        return page.comments.filter(is_visible=True).count()
    return 0


def get_comment_replies(comment: Comment) -> QuerySet[Comment]:
    return comment.replies.filter(is_visible=True)


def get_comment_reply_count(comment: Comment) -> int:
    return comment.replies.filter(is_visible=True).count()


def comment_to_dict(comment: Comment, include_replies: bool = True) -> dict:
    author_profile = comment.author.profile

    replies: list[dict] = []
    if include_replies:
        for reply in get_comment_replies(comment):
            replies.append(comment_to_dict(reply, include_replies=False))

    return {
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
    }


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
