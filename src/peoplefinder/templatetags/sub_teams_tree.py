from django import template
from django.db.models import OuterRef
from django.shortcuts import reverse
from django.utils.html import format_html, mark_safe

from peoplefinder.backports import ArraySubquery
from peoplefinder.models import Team, TeamTree


register = template.Library()


@register.simple_tag
def sub_teams_tree(team: Team) -> str:
    # Build a path array that we can use to sort into a depth-first representation of
    # the team tree.
    path_subquery = (
        TeamTree.objects.select_related("parent")
        .filter(child=OuterRef("pk"))
        .order_by("-depth")
        # `distinct` is required to stop the `order_by` being cleared.
        # https://code.djangoproject.com/ticket/31687
        .distinct("depth")
    )

    # NOTE: The array subquery is added twice because of the filter on `path`. It's
    # possible this might need to be optimised in the future.
    teams = list(
        Team.objects.annotate(
            path=ArraySubquery(path_subquery.values("parent__pk")),
        )
        .filter(path__contains=[team.pk])
        .order_by("path")
    )

    depth = 0

    output = ['<ul class="pf-team-tree pf-team-tree--container">']

    for i, team in enumerate(teams):
        output.append('<li class="pf-team-tree__child">')

        team.depth = len(team.path)

        try:
            next_team = teams[i + 1]
            next_team.depth = len(next_team.path)
        except IndexError:
            next_team = None

        has_children = next_team and (next_team.depth > team.depth)

        if has_children:
            output.append('<strong class="pf-team-tree--with-subgroups">')

        output.append(
            format_html(
                '<a class="govuk-link" href="{}">{}</a>',  # noqa
                reverse("team-view", args=[team.slug]),
                team.name,
            )
        )

        if has_children:
            output.append("</strong>")

            # Don't show the section link if it's the same as the current page.
            if depth > 0:
                output.append(
                    format_html(
                        '[<a class="govuk-link" href="{}">Show this section</a>]',  # noqa
                        reverse("team-tree", args=[team.slug]),
                    )
                )

        # This is the last team.
        if not next_team:
            output.append("</li>")
        # The current team has children.
        elif has_children:
            output.append('<ul class="pf-team-tree">')
        # The current team has no siblings left.
        elif next_team.depth < team.depth:
            output.append("</li>")

            # Unwind back to the depth of the next team.
            for _ in range(team.depth - next_team.depth):
                output.append("</ul>")
                output.append("</li>")
        # The current team has more siblings.
        else:
            output.append("</li>")

        depth = team.depth

    # Unwind back to the root.
    for _ in range(depth):
        output.append("</ul>")
        output.append("</li>")

    output.append("</ul>")

    return mark_safe("\n".join(output))  # noqa
