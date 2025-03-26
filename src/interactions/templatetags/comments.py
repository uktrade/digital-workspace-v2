from django import template
from django.urls import reverse
from wagtail.models import Page

from interactions.services import comments as comments_service
from news.forms import CommentForm


register = template.Library()


@register.inclusion_tag("dwds/components/comments.html", takes_context=True)
def page_comments(context, page: Page):
    comments = []
    for page_comment in comments_service.get_page_comments(page):
        comment = comments_service.comment_to_dict(page_comment)

        comments.append(comment)
    return {
        "user": context["user"],
        "comment_count": comments_service.get_page_comment_count(page),
        "comments": comments,
        "comment_form": CommentForm(),
        "comment_form_url": reverse("interactions:comment-on-page", args=[page.pk]),
        "request": context["request"],
    }


@register.simple_tag
def user_can_delete_comment(user, comment_id):
    return comments_service.can_hide_comment(user, comment_id)


@register.simple_tag
def user_can_edit_comment(user, comment_id):
    return comments_service.can_edit_comment(user, comment_id)
