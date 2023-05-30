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

        if people and not teams:
            url = reverse("search:category", kwargs={"category": "people"})
        elif teams and not people:
            url = reverse("search:category", kwargs={"category": "teams"})
        else:
            url = reverse("search:category", kwargs={"category": "all"})

        r = self.client.get(
            url,
            {"query": query, "filters": filters},
            follow=True,
        )

        assert r.status_code == 200

        return r

    @pytest.mark.opensearch
    def test_updated_profile(self, another_normal_user):
        r = self._search("jane")
        assert str(another_normal_user.profile.slug) in str(r.content)

        another_normal_user.profile.first_name = "Tim"
        another_normal_user.profile.email = "tim.smith@example.com"
        another_normal_user.profile.save()

        call_command("update_index")

        r = self._search("jane")
        assert str(another_normal_user.profile.slug) not in str(r.content)

        r = self._search("tim")
        assert str(another_normal_user.profile.slug) in str(r.content)

    @pytest.mark.opensearch
    def test_search_for_person(self, another_normal_user):
        r = self._search("jane")

        assert b"pf-person-search-result" in r.content
        assert b"pf-team-card" not in r.content

        assert str(another_normal_user.profile.slug) in str(r.content)
        assert b"(1)" in r.content

    # Currently no teams-only search exists

    @pytest.mark.opensearch
    def test_search_for_team(self, another_normal_user):
        r = self._search("software")

        assert b"pf-person-search-result" in r.content
        assert b"pf-team-card" in r.content

        # The normal_user is in the Software team.
        assert str(another_normal_user.profile.slug) in str(r.content)
        assert b"/teams/software/" in r.content
        assert b"(2)" in r.content

    @pytest.mark.opensearch
    def test_search_for_multiple_teams(self):
        r = self._search("S", people=False)

        assert b"pf-person-search-result" not in r.content
        assert b"pf-team-card" in r.content

        assert b"/teams/software/" in r.content
        assert b"/teams/spacex/" in r.content

        assert b"(2)" in r.content
