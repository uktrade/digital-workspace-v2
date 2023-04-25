import re

import bleach
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe


register = template.Library()


add_link_regex = re.compile(r"(https://t.co/[^ ]+)")


@register.filter(needs_autoescape=True)
@stringfilter
def add_twitter_link(text, autoescape=True):
    cleaned = bleach.clean(text)
    if "http:" in cleaned:
        cleaned = cleaned.replace("http", "https")

    return mark_safe(  # noqa S308, S703
        add_link_regex.sub(
            r'<br /><a target="_blank" class="govuk-link" href="\1">View on twitter</a>',
            cleaned,
        )
    )
