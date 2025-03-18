from django import template

from news.services import comment as comment_service


register = template.Library()


@register.simple_tag
def user_can_delete_comment(user, comment):
    return comment_service.can_hide_comment(user, comment)
