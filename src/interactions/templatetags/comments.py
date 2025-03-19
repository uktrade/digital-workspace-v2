from django import template
from django.urls import reverse
from wagtail.models import Page

from interactions.services.comments import (
    can_hide_comment,
    comment_to_dict,
    get_page_comment_count,
    get_page_comments,
)
from news.forms import CommentForm


register = template.Library()


@register.inclusion_tag("dwds/components/comments.html", takes_context=True)
def page_comments(context, page: Page):
    comment_form_submission_url = reverse(
        "interactions:comment-on-page", args=[page.pk]
    )
    comments = []

    for page_comment in get_page_comments(page):
        comment = comment_to_dict(page_comment)
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
        "comment_count": get_page_comment_count(page),
        "comments": comments,
        "comment_form": CommentForm(),
        "comment_form_url": comment_form_submission_url,
        "request": context["request"],
    }


@register.simple_tag
def user_can_delete_comment(user, comment_id):
    return can_hide_comment(user, comment_id)
