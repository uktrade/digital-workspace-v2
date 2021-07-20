from django import template
from django.shortcuts import reverse
from django.utils.html import format_html, mark_safe

from peoplefinder.models import Team, TeamTree

register = template.Library()


@register.simple_tag
def sub_teams_tree(team: Team) -> str:
    team_tree_query = list(
        TeamTree.objects.select_related("child")
        .filter(parent=team)
        .order_by("child", "depth")
    )

    depth = 0

    output = ['<ul class="pf-team-tree pf-team-tree--container">']

    for i, team_tree in enumerate(team_tree_query):
        output.append('<li class="pf-team-tree__child">')

        try:
            next_team_tree = team_tree_query[i + 1]
        except IndexError:
            next_team_tree = None

        has_children = next_team_tree and (next_team_tree.depth > team_tree.depth)

        if has_children:
            output.append('<strong class="pf-team-tree--with-subgroups">')

        output.append(
            format_html(
                '<a class="govuk-link" href="{}">{}</a>',  # noqa
                reverse("team-view", args=[team_tree.child.slug]),
                team_tree.child.name,
            )
        )

        if has_children:
            output.append("</strong>")

            # Don't show the section link if it's the same as the current page.
            if depth > 0:
                output.append(
                    format_html(
                        '[<a class="govuk-link" href="{}">Show this section</a>]',  # noqa
                        reverse("team-tree", args=[team_tree.child.slug]),
                    )
                )

        # This is the last team.
        if not next_team_tree:
            output.append("</li>")
        # The current team has children.
        elif has_children:
            output.append('<ul class="pf-team-tree">')
        # The current team has no siblings left.
        elif next_team_tree.depth < team_tree.depth:
            output.append("</li>")

            # Unwind back to the depth of the next team.
            for _ in range(team_tree.depth - next_team_tree.depth):
                output.append("</ul>")
                output.append("</li>")
        # The current team has more siblings.
        else:
            output.append("</li>")

        depth = team_tree.depth

    # Unwind back to the root.
    for _ in range(depth):
        output.append("</ul>")
        output.append("</li>")

    output.append("</ul>")

    return mark_safe("\n".join(output))
