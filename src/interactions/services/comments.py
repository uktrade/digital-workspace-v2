from django.shortcuts import get_object_or_404
from news.models import Comment


def edit_comment(content: str, pk: str) -> None:
    comment = get_object_or_404(Comment, id=pk)
    if comment:
        comment.content = content
        comment.save()
