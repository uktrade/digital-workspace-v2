from news.models import Comment
from user.models import User


def show_comment(comment: Comment) -> None:
    comment.is_visible = True
    comment.save(update_fields=["is_visible"])


def hide_comment(comment: Comment) -> None:
    comment.is_visible = False
    comment.save(update_fields=["is_visible"])


def can_hide_comment(user: User, comment: Comment) -> bool:
    return user == comment.author
