from django.db.models import QuerySet
from wagtail.models import Page

from news.models import Comment
from user.models import User


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
        return page.comments.filter(parent_id=None, is_visible=True).order_by("-posted_date")
    return Comment.objects.none()


def get_page_comment_count(page: Page) -> int:
    if hasattr(page, "comments"):
        return page.comments.count()
    return 0


def get_comment_replies(comment: Comment) -> QuerySet[Comment]:
    return comment.replies.all()


def get_comment_reply_count(comment: Comment) -> int:
    return comment.replies.count()


def comment_to_dict(comment: Comment, include_replies: bool = True) -> dict:
    author_profile = comment.author.profile

    replies: list[dict] = []
    if include_replies:
        for reply in get_comment_replies(comment):
            replies.append(comment_to_dict(reply, include_replies=False))

    return {
        "author_name": author_profile.full_name,
        "author_url": "https://gov.uk/",
        "author_image_url": (
            author_profile.photo.url if author_profile.photo else None
        ),
        "posted_date": comment.posted_date,
        "message": comment.content,
        "show_replies": include_replies,
        "reply_count": get_comment_reply_count(comment),
        "replies": replies,
    }
