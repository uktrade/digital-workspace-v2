from django import template
from django.shortcuts import get_object_or_404
from django.urls import reverse
from wagtail.models import Page

from interactions.services import comments as comments_service
from news.forms import CommentForm
from news.models import Comment


register = template.Library()


@register.inclusion_tag("dwds/components/comments.html", takes_context=True)
def page_comments(context, page: Page):
    comment_form_submission_url = reverse(
        "interactions:comment-on-page", args=[page.pk]
    )
    comments = []
    for page_comment in comments_service.get_page_comments(page):
        comment = comments_service.comment_to_dict(page_comment)
        comment.update(
            reply_form=CommentForm(
                initial={"in_reply_to": page_comment.pk},
                auto_id="reply_%s",
            ),
            reply_form_url=comment_form_submission_url,
        )
        comments.append(comment)
    return {
        "user": context["user"],
        "comment_count": comments_service.get_page_comment_count(page),
        "comments": comments,
        "comment_form": CommentForm(),
        "comment_form_url": comment_form_submission_url,
        "request": context["request"],
        "page": page,
    }


@register.simple_tag
def user_can_delete_comment(user, comment_id):
    return comments_service.can_hide_comment(user, comment_id)


@register.simple_tag
def user_can_edit_comment(user, comment_id):
    return comments_service.can_edit_comment(user, comment_id)


@register.inclusion_tag("interactions/edit_comment_input.html", takes_context=True)
def edit_comment_input(context, comment_id: int):
    comment = get_object_or_404(Comment, id=comment_id)
    comment_dict = comments_service.comment_to_dict(comment)
    comment_dict.update(
        edit_comment_form_url=reverse(
            "interactions:edit-comment-form",
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

    return {
        "user": context["user"],
        "comment": comment_dict,
        "request": context["request"],
    }
