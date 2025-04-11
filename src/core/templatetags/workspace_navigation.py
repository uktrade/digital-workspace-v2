from django import template
from django.urls import reverse
from wagtail.models import Page

from peoplefinder.models import Person, Team
from peoplefinder.services.team import TeamService


register = template.Library()


def build_home_breadcrumbs(request) -> list[tuple[str, str]]:
    home_page = Page.objects.get(slug="home")
    return [(home_page.get_url(request), home_page.title)]


def build_team_breadcrumbs(request, team: Team) -> list[tuple[str, str]]:
    breadcrumbs = build_home_breadcrumbs(request)

    parent_teams = TeamService().get_all_parent_teams(team)
    breadcrumbs += [
        (reverse("team-view", args=[parent_team.slug]), parent_team.short_name)
        for parent_team in parent_teams
    ]
    breadcrumbs += [(reverse("team-view", args=[team.slug]), team.short_name)]

    return breadcrumbs


@register.inclusion_tag("tags/breadcrumbs.html", takes_context=True)
def breadcrumbs(context) -> list[tuple[str, str]]:
    """Shows a breadcrumb list based on a page's ancestors"""
    request = context["request"]
    breadcrumbs = []
    extra_breadcrumbs = context.get("extra_breadcrumbs", [])

    self = context.get("self")
    # Don't display breadcrumbs if the page isn't nested deeply enough (e.g. homepage)
    if self and self.depth > 2:
        ancestors = Page.objects.ancestor_of(self, inclusive=True).filter(depth__gt=1)
        breadcrumbs = [
            (ancestor.get_url(request), ancestor.title) for ancestor in ancestors
        ]
        return {"breadcrumbs": breadcrumbs + extra_breadcrumbs}
    has_team_breadcrumbs = context.get("team_breadcrumbs", False)
    has_profile_breadcrumbs = context.get("profile_breadcrumbs", False)

    # Build team breadcrumbs
    if has_team_breadcrumbs or has_profile_breadcrumbs:
        if has_team_breadcrumbs:
            team: Team | None = context.get("team", None)
            if team:
                breadcrumbs = build_team_breadcrumbs(request, team)
            else:
                breadcrumbs = build_home_breadcrumbs(request)
            return {"breadcrumbs": breadcrumbs + extra_breadcrumbs}

        # Build profile breadcrumbs
        if has_profile_breadcrumbs:
            team: Team | None = context.get("team", None)
            if team:
                breadcrumbs = build_team_breadcrumbs(request, team)
            else:
                breadcrumbs = build_home_breadcrumbs(request)

            profile: Person = context["profile"]
            breadcrumbs.append(
                (reverse("profile-view", args=[profile.slug]), profile.full_name)
            )
            return {"breadcrumbs": breadcrumbs + extra_breadcrumbs}

    return {"breadcrumbs": breadcrumbs + extra_breadcrumbs}
