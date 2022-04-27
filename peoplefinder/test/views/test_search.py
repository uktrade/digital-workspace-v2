import pytest
from django.urls import reverse

from peoplefinder.models import Team


class TestSearchView:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client, normal_user):
        self.client = client
        self.client.force_login(normal_user)

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

    # Search is tricky to test because OpenSearch is being shared between tests and
    # local. The database creates it's own test database, but we don't have the same
    # mechanism with OpenSearch.
    @pytest.mark.skip(reason="Testing search is currently flaky")
    def test_search_for_person(self, normal_user):
        r = self._search("john")

        assert r.context["person_matches"] == [normal_user.profile]
        assert r.context["team_matches"] == []
        assert r.context["total_matches"] == 1

    @pytest.mark.skip(reason="Testing search is currently flaky")
    def test_search_for_team(self):
        r = self._search("software")

        assert r.context["person_matches"] == []
        assert r.context["team_matches"] == [Team.objects.get(name="Software")]
        assert r.context["total_matches"] == 1

    @pytest.mark.skip(reason="Testing search is currently flaky")
    def test_search_for_multiple_teams(self):
        r = self._search("S", people=False)

        assert r.context["person_matches"] == []
        assert r.context["team_matches"] == [
            Team.objects.get(name="SpaceX"),
            Team.objects.get(name="Software"),
        ]
        assert r.context["total_matches"] == 2
