from typing import Iterator, Optional, TypedDict

from django.contrib.postgres.aggregates import ArrayAgg
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import (
    Case,
    CharField,
    F,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Concat
from django.utils.text import slugify

from peoplefinder.models import AuditLog, Person, Team, TeamMember, TeamTree
from peoplefinder.services.audit_log import (
    AuditLogSerializer,
    AuditLogService,
    ObjectRepr,
)
from user.models import User


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

    def get_all_child_teams(self, parent: Team) -> QuerySet[Team]:
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

        team_tree_depth_1 = TeamTree.objects.select_related("child", "parent").filter(
            depth=1
        )

        children_subquery = Subquery(
            team_tree_depth_1.filter(depth=1, parent__pk=OuterRef("child__pk")).values(
                "child"
            )[:1],
        )

        full_team_tree = team_tree_depth_1.annotate(
            children_subquery=children_subquery,
            has_children=Case(
                When(
                    Q(children_subquery__isnull=False),
                    then=Value(True),
                ),
                default=Value(False),
            ),
        ).order_by("-has_children", "parent__name", "child__name")

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

    def can_team_be_deleted(self, team: Team) -> tuple[bool, list[str]]:
        """Check and return whether a team can be deleted.

        Args:
            team (Team): The team to be deleted.

        Returns:
            tuple[bool, list[str]]: Whether the team can be deleted and the reasons why.
        """
        reasons = []

        sub_teams = self.get_all_child_teams(team)
        if sub_teams:
            reasons.append("sub-teams")

        has_members = self.get_team_members(team).exists()
        if has_members:
            reasons.append("members")

        if reasons:
            return False, reasons

        return True, []

    def team_created(self, team: Team, created_by: Optional[User]) -> None:
        """A method to be called after a team has been created.

        Always call this after you create a team, unless you need to bypass the hook.

        Args:
            team: The team that was created.
            created_by: Who created the team.
        """
        AuditLogService.log(AuditLog.Action.CREATE, created_by, team)

    def team_updated(self, team: Team, updated_by: User) -> None:
        """A method to be called after a team has been updated.

        Always call this after you update a team, unless you need to bypass the hook.

        Args:
            team: The team that was updated.
            updated_by: Who updated the team.
        """
        AuditLogService.log(AuditLog.Action.UPDATE, updated_by, team)

    def team_deleted(self, team: Team, deleted_by: User) -> None:
        """A method to be called after a team has been deleted.

        Always call this after you delete a team, unless you need to bypass the hook.

        Args:
            team: The team that was deleted.
            deleted_by: Who deleted the team.
        """
        AuditLogService.log(AuditLog.Action.DELETE, deleted_by, team)

    def get_team_members(self, team: Team) -> QuerySet[TeamMember]:
        sub_teams = self.get_all_child_teams(team)

        return TeamMember.active.filter(Q(team=team) | Q(team__in=sub_teams))

    def get_profile_completion_cache_key(self, team_pk: int) -> str:
        return f"team_{team_pk}__profile_completion"

    def clear_profile_completion_cache(self, team_pk: int):
        cache.delete(self.get_profile_completion_cache_key(team_pk))

    def profile_completion(self, team: Team) -> float | None:
        """
        Calculate the percentage of users in the team with 100% profile
        completion.

        Returns:
            float: A percentage
        """
        cache_key = self.get_profile_completion_cache_key(team.pk)
        if cached_value := cache.get(cache_key, None):
            return cached_value

        # Get all people from all teams
        people = Person.objects.filter(
            id__in=Subquery(self.get_team_members(team).values("person_id"))
        )
        completed_profiles = people.filter(profile_completion__gte=100)

        total_members = len(people)
        total_completed_profiles = len(completed_profiles)

        if total_members == 0:
            return None

        completed_profile_percent = total_completed_profiles / total_members

        # Cache the result for an hour.
        timeout = 60 * 60
        cache.set(cache_key, completed_profile_percent, timeout)
        return completed_profile_percent


class TeamAuditLogSerializer(AuditLogSerializer):
    model = Team

    assert len(Team._meta.get_fields()) == 13, (
        "It looks like you have updated the `Team` model. Please make sure you have"
        " updated `TeamAuditLogSerializer.serialize` to reflect any field changes."
    )

    def serialize(self, instance: Team) -> ObjectRepr:
        team = (
            Team.objects.filter(pk=instance.pk)
            .values()
            .annotate(
                # TODO: Move to a team query set manager method.
                leaders_positions=ArrayAgg(
                    Concat(
                        F("members__leaders_position") + 1,
                        Value(": "),
                        "members__person__first_name",
                        Value(" "),
                        "members__person__last_name",
                        output_field=CharField(),
                    ),
                    filter=(
                        Q(leaders_ordering=Team.LeadersOrdering.CUSTOM)
                        & Q(members__head_of_team=True)
                    ),
                    ordering="members__leaders_position",
                )
            )[0]
        )

        if parent := TeamService().get_immediate_parent_team(instance):
            team["parent"] = parent.name

        del team["created_at"]
        del team["updated_at"]

        return team
