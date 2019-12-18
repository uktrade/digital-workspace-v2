from django import template

from wagtail.core.models import Page

register = template.Library()

@register.inclusion_tag("tags/breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    """Shows a breadcrumb list based on a page's ancestors"""

    self = context.get("self")

    if self is None or self.depth <= 2:
        # Don't display breadcrumbs if the page isn't nested deeply enough (e.g. homepage)
        ancestors = ()
    else:
        ancestors = Page.objects.ancestor_of(self, inclusive=True).filter(depth__gt=1)

    return {
        "ancestors": ancestors,
        "request": context["request"]
    }
