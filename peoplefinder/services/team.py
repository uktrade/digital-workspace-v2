from typing import Iterator, Optional, TypedDict

from django.db import connection, transaction
from django.db.models import QuerySet, Subquery
from django.utils.text import slugify

from peoplefinder.models import Team, TeamTree


class TeamSelectDatum(TypedDict):
    team_id: int
    team_name: str
    parent_id: Optional[int]
    parent_name: Optional[str]


class TeamServiceError(Exception):
    pass


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

    def validate_team_parent_update(self, team: Team, parent: Team) -> None:
        """Validate that the new parent is valid for the given team.

        Args:
            team (Team):The team to be updated.
            parent (Team): The given parent team.

        Raises:
            TeamServiceError: If team's parent is not a valid parent.
        """
        if parent == team:
            raise TeamServiceError("A team's parent cannot be the team itself")

        if parent in self.get_all_child_teams(team):
            raise TeamServiceError("A team's parent cannot be a team's child")

        if parent and (team == self.get_root_team()):
            raise TeamServiceError("Cannot update the parent of the root team")

    @transaction.atomic
    def update_team_parent(self, team: Team, parent: Team) -> None:
        """Update a team's parent with the given parent team.

        The implementation was informed by the following blog:
        https://www.percona.com/blog/2011/02/14/moving-subtrees-in-closure-table/

        Args:
            team (Team): The team to be updated.
            parent (Team): The given parent team.
        """
        self.validate_team_parent_update(team, parent)

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

    def get_team_select_data(self) -> Iterator[TeamSelectDatum]:
        """Return the teams data for the team-select web component.

        Yields:
            dict of team select data
        """
        root_team = self.get_root_team()
        full_team_tree = (
            TeamTree.objects.select_related("child")
            .filter(depth=1)
            .order_by("child", "depth")
        )

        yield {
            "team_id": root_team.id,
            "team_name": root_team.name,
            "parent_id": None,
            "parent_name": None,
        }

        for team_node in full_team_tree:
            yield {
                "team_id": team_node.child.id,
                "team_name": team_node.child.name,
                "parent_id": team_node.parent.id,
                "parent_name": team_node.parent.name,
            }

    def generate_team_slug(self, team: Team) -> str:
        """Return a new slug for the given team.

        Args:
            team (Team): The given team.

        Raises:
            TeamServiceError: If a unique team slug cannot be generated.

        Returns:
            str: A new slug for the team.
        """
        slug = slugify(team.name)

        duplicate_slugs = Team.objects.filter(slug=slug).exclude(pk=team.pk).exists()

        # If the new slug isn't unique then append the parent team's name to the front.
        # Note that if the parent team's name changes it won't be reflected here in the
        # new slug.
        if duplicate_slugs:
            parent_team = self.get_immediate_parent_team(team)

            if not parent_team:
                raise TeamServiceError("Cannot generate unique team slug")

            slug = slugify(f"{parent_team.name} {team.name}")

        return slug
