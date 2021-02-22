from django import template
from django.utils.html import format_html, mark_safe

from peoplefinder.models import Team, TeamTree

register = template.Library()


@register.simple_tag
def sub_teams_tree(team: Team) -> str:
    team_tree_query = (
        TeamTree.objects.select_related("child")
        .filter(parent=team)
        .order_by("child", "depth")
    )

    output = ["<ul>"]

    prev_depth = 0

    for team_tree in team_tree_query:
        if team_tree.depth > prev_depth:
            output.append("<ul>")
        elif team_tree.depth < prev_depth:
            output.append("</ul>")

        output.append(
            format_html(
                '<li><a class="govuk-link" href="{}">{}</a></li>',  # noqa
                f"/teams/{team_tree.child.slug}",
                team_tree.child.name,
            )
        )

        prev_depth = team_tree.depth

    output.append("</ul>")

    return mark_safe("\n".join(output))
