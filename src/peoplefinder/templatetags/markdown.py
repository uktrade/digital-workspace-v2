import markdown as markdown_lib
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter(needs_autoescape=True)
def markdown(text: str, autoescape=True):
    # Remove any javascript: or data: from the text to prevent XSS
    text = text.replace("javascript:", "")
    text = text.replace("data:", "")

    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x  # noqa E731

    html = markdown_lib.markdown(esc(text), output_format="html5")

    return mark_safe(html)  # noqa S703
