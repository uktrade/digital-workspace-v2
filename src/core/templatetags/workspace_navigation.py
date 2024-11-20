from django import template
from django.urls import reverse
from wagtail.models import Page


register = template.Library()


@register.inclusion_tag("tags/breadcrumbs.html", takes_context=True)
def breadcrumbs(context) -> list[tuple[str, str]]:
    """Shows a breadcrumb list based on a page's ancestors"""
    request = context["request"]
    breadcrumbs = []

    self = context.get("self")
    # Don't display breadcrumbs if the page isn't nested deeply enough (e.g. homepage)
    if self and self.depth > 2:
        ancestors = Page.objects.ancestor_of(self, inclusive=True).filter(depth__gt=1)
        breadcrumbs = [
            (ancestor.get_url(request), ancestor.title) for ancestor in ancestors
        ]
        return {"breadcrumbs": breadcrumbs}

    # Build team breadcrumbs
    if context.get("team_breadcrumbs", False):
        team = context["team"]
        home_page = Page.objects.get(slug="home")
        breadcrumbs = [(home_page.get_url(request), home_page.title)]

        parent_teams = context.get("parent_teams", [])
        breadcrumbs += [
            (reverse("team-view", args=[parent_team.slug]), parent_team.short_name)
            for parent_team in parent_teams
        ]

        breadcrumbs += [(reverse("team-view", args=[team.slug]), team.short_name)]
        return {"breadcrumbs": breadcrumbs}

    return {"breadcrumbs": breadcrumbs}
