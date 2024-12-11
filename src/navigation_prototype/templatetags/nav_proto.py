from django import template

from navigation_prototype.models import Nav

register = template.Library()


@register.inclusion_tag("navigation_prototype/navigation.html")
def nav_proto():
    try:
        nav = Nav.objects.first()
    except Nav.DoesNotExist:
        return {}

    return {
        "primary_links": nav.links.all(),
    }
