from news.models import Comment


class CommentNotFound(Exception): ...


def edit_comment(content: str, pk: str) -> None:
    try:
        comment = Comment.objects.get(pk=pk)
    except Comment.DoesNotExist:
        raise CommentNotFound()

    if comment:
        comment.content = content
        comment.save()
