from peoplefinder.models import Team
from peoplefinder.services.team import TeamService
from peoplefinder.views.api.team import TeamSerializer, TeamView


def test_team_serializer(db, software_team):
    team_service = TeamService()
    team = software_team

    team = TeamView().get_queryset().get(pk=team.pk)
    serialized_team = TeamSerializer(team)
    all_parents = team_service.get_all_parent_teams(team)
    parent = team_service.get_immediate_parent_team(team)

    assert serialized_team.data["parent_id"] == parent.pk
    assert serialized_team.data["ancestry"] == "/".join(
        [str(x.pk) for x in all_parents]
    )
