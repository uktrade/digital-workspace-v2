import pytest
from pytest_django.asserts import assertContains, assertNotContains
from django.core.management import call_command
from django.urls import reverse


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
        assertContains(r, str(another_normal_user.profile.slug))

        another_normal_user.profile.first_name = "Tim"
        another_normal_user.profile.email = "tim.smith@example.com"
        another_normal_user.profile.save()

        call_command("update_index")

        r = self._search("jane")
        assertNotContains(r, str(another_normal_user.profile.slug))

        r = self._search("tim")
        assertContains(r, str(another_normal_user.profile.slug))

    @pytest.mark.opensearch
    def test_search_for_person(self, another_normal_user):
        r = self._search("jane")

        assertContains(r, "pf-person-search-result")
        assertNotContains(r, "pf-team-card")

        assertContains(r, str(another_normal_user.profile.slug))
        assertContains(r, "(1)")

    # Currently no teams-only search exists

    @pytest.mark.opensearch
    def test_search_for_team(self, another_normal_user):
        r = self._search("software")

        assertContains(r, "pf-person-search-result")
        assertContains(r, "pf-team-card")

        # The normal_user is in the Software team.
        assertContains(r, str(another_normal_user.profile.slug))
        assertContains(r, "/teams/software/")
        assertContains(r, "(2)")

    @pytest.mark.opensearch
    def test_search_for_multiple_teams(self):
        r = self._search("S", people=False)

        assertNotContains(r, "pf-person-search-result")
        assertContains(r, "pf-team-card")

        assertContains(r, "/teams/software/")
        assertContains(r, "/teams/spacex/")

        assertContains(r, "(2)")
