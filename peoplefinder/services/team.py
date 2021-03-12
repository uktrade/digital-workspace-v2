from typing import Optional

from django.db import connection, transaction
from django.db.models import QuerySet, Subquery

from peoplefinder.models import Team, TeamTree


class TeamService:
    def add_team(self, team: Team, parent: Team) -> None:
        """Add a team into the hierarchy.

        Args:
            team (Team): The team to be added.
            parent (Team): The parent team.
        """
        TeamTree.objects.bulk_create(
            [
                # reference to itself
                TeamTree(parent=team, child=team, depth=0),
                # all required tree connections
                *(
                    TeamTree(parent=tt.parent, child=team, depth=tt.depth + 1)
                    for tt in TeamTree.objects.filter(child=parent)
                ),
            ]
        )

    @transaction.atomic
    def update_team_parent(self, team: Team, parent: Team) -> None:
        """Update a team's parent with the given parent team.

        The implementation was informed by the following blog:
        https://www.percona.com/blog/2011/02/14/moving-subtrees-in-closure-table/

        Args:
            team (Team): The team to be updated.
            parent (Team): The given parent team.
        """
        TeamTree.objects.filter(
            child__in=Subquery(TeamTree.objects.filter(parent=team).values("child"))
        ).exclude(
            parent__in=Subquery(TeamTree.objects.filter(parent=team).values("child"))
        ).delete()

        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO peoplefinder_teamtree (parent_id, child_id, depth)
                SELECT
                    supertree.parent_id,
                    subtree.child_id,
                    (supertree.depth + subtree.depth + 1)
                FROM peoplefinder_teamtree AS supertree
                CROSS JOIN peoplefinder_teamtree AS subtree
                WHERE
                    subtree.parent_id = %s
                    AND supertree.child_id = %s
                """,
                [team.id, parent.id],
            )

    def get_all_child_teams(self, parent: Team) -> QuerySet:
        """Return all child teams of the given parent team.

        Args:
            parent (Team): The given parent team.

        Returns:
            QuerySet: A queryset of teams.
        """
        return Team.objects.filter(children__parent=parent).exclude(
            children__child=parent
        )

    def get_immediate_child_teams(self, parent: Team) -> QuerySet:
        """Return all immediate child teams of the given parent team.

        Args:
            parent (Team): The given parent team.

        Returns:
            QuerySet: A queryset of teams.
        """
        return Team.objects.filter(children__parent=parent, children__depth=1)

    def get_all_parent_teams(self, child: Team) -> QuerySet:
        """Return all parent teams for the given child team.

        Args:
            child (Team): The given child team.

        Returns:
            QuerySet: A query of teams.
        """
        return (
            Team.objects.filter(parents__child=child).exclude(parents__parent=child)
            # TODO: Not sure if we should order here or at the call sites.
            .order_by("-parents__depth")
        )

    def get_immediate_parent_team(self, child: Team) -> Optional[Team]:
        """Return the immediate parent team for the given team.

        Args:
            child (Team): The given team.

        Returns:
            Team: The immediate parent team.
        """
        try:
            return Team.objects.filter(parents__child=child, parents__depth=1).get()
        except Team.DoesNotExist:
            return None

    def get_root_team(self) -> Team:
        """Return the root team.

        Returns:
            Team: The root team.
        """
        teams_with_parents = TeamTree.objects.filter(depth__gt=0)

        return Team.objects.exclude(
            id__in=Subquery(teams_with_parents.values("child"))
        ).get()
