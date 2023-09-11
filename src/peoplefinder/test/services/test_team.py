import unittest

import pytest

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService, TeamServiceError


# TODO: Break up into individual tests.
def test_team_service(db):
    """
    .
    └── DIT
        ├── COO
        │   ├── Analysis
        │   └── Change
        └── GTI
            └── DEFEND
            ├── Investment
    """
    test_case = unittest.TestCase()

    # We need to start from fresh for these tests.
    Team.objects.all().delete()

    team_service = TeamService()

    dit = Team.objects.create(name="DIT", slug="dit")
    coo = Team.objects.create(name="COO", slug="coo")
    gti = Team.objects.create(name="GTI", slug="gti")
    team_service.add_team(team=dit, parent=dit)
    team_service.add_team(team=coo, parent=dit)
    team_service.add_team(team=gti, parent=dit)

    coo_analysis = Team.objects.create(name="Analysis", slug="analysis")
    coo_change = Team.objects.create(name="Change", slug="change")
    team_service.add_team(team=coo_analysis, parent=coo)
    team_service.add_team(team=coo_change, parent=coo)

    gti_investment = Team.objects.create(name="Investment", slug="investment")
    gti_defence = Team.objects.create(name="DEFEND", slug="defend")
    team_service.add_team(team=gti_investment, parent=gti)
    team_service.add_team(team=gti_defence, parent=gti)

    test_case.assertCountEqual(
        list(team_service.get_all_child_teams(parent=dit)),
        [
            coo,
            gti,
            coo_analysis,
            coo_change,
            gti_investment,
            gti_defence,
        ],
    )

    test_case.assertCountEqual(
        list(team_service.get_immediate_child_teams(parent=dit)), [coo, gti]
    )

    test_case.assertCountEqual(
        list(team_service.get_all_parent_teams(child=coo_change)), [dit, coo]
    )

    assert team_service.get_root_team() == dit

    assert team_service.get_immediate_parent_team(gti_defence) == gti

    # test update
    team_service.update_team_parent(gti, coo)

    assert team_service.get_immediate_parent_team(gti) == coo

    test_case.assertCountEqual(
        list(team_service.get_all_child_teams(coo)),
        [
            gti,
            coo_analysis,
            coo_change,
            gti_investment,
            gti_defence,
        ],
    )

    test_case.assertCountEqual(list(team_service.get_immediate_child_teams(dit)), [coo])

    # revert update
    team_service.update_team_parent(gti, dit)

    assert team_service.get_immediate_parent_team(gti) == dit

    # test team select methods
    assert list(team_service.get_team_select_data()) == [
        {
            "team_id": dit.id,
            "team_name": dit.name,
            "parent_id": None,
            "parent_name": None,
        },
        {
            "team_id": coo.id,
            "team_name": coo.name,
            "parent_id": dit.id,
            "parent_name": dit.name,
        },
        {
            "team_id": gti.id,
            "team_name": gti.name,
            "parent_id": dit.id,
            "parent_name": dit.name,
        },
        {
            "team_id": coo_analysis.id,
            "team_name": coo_analysis.name,
            "parent_id": coo.id,
            "parent_name": coo.name,
        },
        {
            "team_id": coo_change.id,
            "team_name": coo_change.name,
            "parent_id": coo.id,
            "parent_name": coo.name,
        },
        {
            "team_id": gti_defence.id,
            "team_name": gti_defence.name,
            "parent_id": gti.id,
            "parent_name": gti.name,
        },
        {
            "team_id": gti_investment.id,
            "team_name": gti_investment.name,
            "parent_id": gti.id,
            "parent_name": gti.name,
        },
    ]

    # test `validate_team_parent_update` through `update_team_parent`
    with pytest.raises(
        TeamServiceError, match="A team's parent cannot be the team itself"
    ):
        team_service.update_team_parent(gti, gti)

    with pytest.raises(
        TeamServiceError, match="A team's parent cannot be a team's child"
    ):
        team_service.update_team_parent(gti, gti_investment)

    with pytest.raises(
        TeamServiceError, match="Cannot update the parent of the root team"
    ):
        team_service.update_team_parent(dit, Team(name="Test"))

    # test `generate_team_slug`
    assert team_service.generate_team_slug(coo_analysis) == "analysis"

    coo_analysis.name = "investment"

    assert team_service.generate_team_slug(coo_analysis) == "coo-investment"

    coo_analysis.name = "analysis"
