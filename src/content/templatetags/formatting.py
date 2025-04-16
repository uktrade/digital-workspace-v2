from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import mark_safe
from django.utils.safestring import SafeString

from content.utils import truncate_words_and_chars


register = template.Library()


@register.filter
@stringfilter
def preview(value):
    parts = value.split(" ")
    return " ".join(parts[0:40])


@register.filter
@stringfilter
def truncate_magic(value, words: int | None = None, chars: int | None = None):
    extra_kwargs = {
        "html": False,
    }
    if words is not None:
        extra_kwargs["words"] = words
    if chars is not None:
        extra_kwargs["chars"] = chars

    return truncate_words_and_chars(
        text=value,
        **extra_kwargs,
    )


@register.filter
@stringfilter
def truncate_magic_html(value, words: int | None = None, chars: int | None = None):
    if not isinstance(value, SafeString):
        return value

    extra_kwargs = {
        "html": True,
    }
    if words is not None:
        extra_kwargs["words"] = words
    if chars is not None:
        extra_kwargs["chars"] = chars

    return mark_safe(  # noqa: S308
        truncate_words_and_chars(
            text=value,
            **extra_kwargs,
        )
    )
