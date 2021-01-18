import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


add_link_regex = re.compile(r"(https://t.co/[^ ]+)")


@register.filter(needs_autoescape=True)
@stringfilter
def add_twitter_link(text, autoescape=True):
    return mark_safe(
        add_link_regex.sub(
            r'<br /><a target="_blank" class="govuk-link" href="\1">View on twitter</a>',
            text,
        )
    )
