import pytest
from django.core.management import call_command
from django.urls import reverse

from peoplefinder.models import Team


class TestSearchView:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client, normal_user):
        self.client = client
        self.client.force_login(normal_user)

        call_command("update_index")

    def _search(self, query, teams=True, people=True):
        filters = []

        if teams:
            filters.append("teams")

        if people:
            filters.append("people")

        r = self.client.get(
            reverse("people-and-teams-search"),
            {"query": query, "filters": filters},
        )

        assert r.status_code == 200

        return r

    @pytest.mark.opensearch
    def test_updated_profile(self, normal_user):
        r = self._search("john")
        assert r.context["person_matches"] == [normal_user.profile]

        normal_user.profile.first_name = "Tim"
        normal_user.profile.save()

        call_command("update_index")

        r = self._search("john")
        assert r.context["person_matches"] == []

        r = self._search("tim")
        assert r.context["person_matches"] == [normal_user.profile]

    @pytest.mark.opensearch
    def test_search_for_person(self, normal_user):
        r = self._search("john")

        assert r.context["person_matches"] == [normal_user.profile]
        assert r.context["team_matches"] == []
        assert r.context["total_matches"] == 1

    @pytest.mark.opensearch
    def test_search_for_team(self, normal_user):
        r = self._search("software")

        # The normal_user is in the Software team.
        assert r.context["person_matches"] == [normal_user.profile]
        assert r.context["team_matches"] == [Team.objects.get(name="Software")]
        assert r.context["total_matches"] == 2

    @pytest.mark.opensearch
    def test_search_for_multiple_teams(self):
        r = self._search("S", people=False)

        assert r.context["person_matches"] == []
        assert r.context["team_matches"] == [
            Team.objects.get(name="SpaceX"),
            Team.objects.get(name="Software"),
        ]
        assert r.context["total_matches"] == 2
