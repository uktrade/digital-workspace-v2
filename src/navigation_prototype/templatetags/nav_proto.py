from django import template

from navigation_prototype.models import Nav


register = template.Library()


@register.inclusion_tag("navigation_prototype/navigation.html")
def nav_proto():
    nav = Nav.objects.first()

    if not nav:
        return {}

    return {
        "primary_links": nav.links.all(),
    }
