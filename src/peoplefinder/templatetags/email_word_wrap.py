from django import template


register = template.Library()


@register.simple_tag
def email_word_wrap() -> str:
    ...