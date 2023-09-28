import pytest
from django.core.management import call_command
from django.urls import reverse

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService
from user.test.factories import UserFactory


class TestTeamEditView:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client, team_admin_user):
        self.client = client
        self.client.force_login(team_admin_user)

    def test_load_page(self, team_admin_user):
        r = self.client.get(reverse("team-edit", kwargs={"slug": "software"}))
        assert r.status_code == 200

    def test_order_team_leaders(self, team_admin_user, software_team):
        red_leader = UserFactory(
            first_name="Red",
            last_name="Leader",
            email="red.leader@example.com",  # /PS-IGNORE
            legacy_sso_user_id=None,
            username="red-leader",
            sso_contact_email="red.leader@example.com",  # /PS-IGNORE
        )
        gold_leader = UserFactory(
            first_name="Gold",
            last_name="Leader",
            email="gold.leader@example.com",  # /PS-IGNORE
            legacy_sso_user_id=None,
            username="gold-leader",
            sso_contact_email="gold.leader@example.com",  # /PS-IGNORE
        )

        call_command("create_user_profiles")

        red_leader_role, _ = red_leader.profile.roles.get_or_create(
            team=software_team,
            job_title="Product Manager",
            head_of_team=True,
        )
        gold_leader_role, _ = gold_leader.profile.roles.get_or_create(
            team=software_team,
            job_title="Delivery Manager",
            head_of_team=True,
        )

        r = self.client.get(reverse("team-edit", kwargs={"slug": "software"}))

        assert (
            r.context["team_leaders_order_component"]["ordering"]
            == Team.LeadersOrdering.ALPHABETICAL
        )

        members = r.context["team_leaders_order_component"]["members"]

        assert len(members) == 2
        assert members[0]["pk"] == gold_leader_role.pk
        assert members[1]["pk"] == red_leader_role.pk

        r = self.client.post(
            reverse("team-edit", kwargs={"slug": "software"}),
            data={
                "name": software_team.name,
                "abbreviation": software_team.abbreviation or "",
                "description": software_team.description,
                "parent_team": (
                    TeamService().get_immediate_parent_team(software_team).pk
                ),
                "leaders_ordering": Team.LeadersOrdering.CUSTOM,
                "leaders_positions": ",".join(
                    map(str, [red_leader_role.pk, gold_leader_role.pk])
                ),
            },
            follow=True,
        )
        assert r.status_code == 200

        red_leader_role.refresh_from_db()
        gold_leader_role.refresh_from_db()

        assert red_leader_role.leaders_position == 0
        assert gold_leader_role.leaders_position == 1
