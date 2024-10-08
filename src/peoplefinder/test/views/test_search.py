import datetime

import pytest
from django.core.management import call_command
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from peoplefinder.models import UkStaffLocation


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
        another_normal_user.profile.preferred_first_name = "Tim"
        another_normal_user.profile.email = "tim.smith@example.com"  # /PS-IGNORE
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
    def test_search_for_team(self, normal_user):
        r = self._search("software")

        assertContains(r, "pf-person-search-result")
        assertContains(r, "pf-team-card")

        # The normal_user is in the Software team.
        assertContains(r, str(normal_user.profile.slug))
        assertContains(r, "/teams/software/")
        assertContains(r, "(2)")

    @pytest.mark.skip(
        reason=(
            "Partial searches are not yet supported, see Search Improvements"
            " PR https://github.com/uktrade/digital-workspace-v2/pull/416"
        )
    )
    @pytest.mark.opensearch
    def test_search_for_multiple_teams(self):
        r = self._search("S", people=False)

        assertNotContains(r, "pf-person-search-result")
        assertContains(r, "pf-team-card")

        assertContains(r, "/teams/software/")
        assertContains(r, "/teams/spacex/")

        assertContains(r, "(2)")

    @pytest.mark.opensearch
    def test_search_on_office_location(self, another_normal_user):
        # Given there is a uk office in Ilfracombe
        office = UkStaffLocation.objects.create(
            code="6ab9caa6",
            name="Ilfracombe",
            city="North Devon",
            organisation="Department for Business and Trade",
        )
        # And there is a user at that office
        another_normal_user.profile.uk_office_location = office
        another_normal_user.profile.save()
        # And the search index has been updated
        call_command("update_index")
        # When I perform a search for people at that office
        resp = self._search("ilfracombe", teams=False)
        # Then the user is returned in the search results
        assert another_normal_user.profile in resp.context["search_results"].object_list

    @pytest.mark.opensearch
    def test_search_for_recently_inactive_person(self, another_normal_user):
        profile = another_normal_user.profile
        ten_days_ago = datetime.datetime.now() - datetime.timedelta(days=10)
        # Given a user that has recently become inactive
        profile.is_active = False
        profile.became_inactive = ten_days_ago
        profile.save()
        # And the search index has been updated
        call_command("update_index")
        # When I perform a search for that user
        resp = self._search("jane", teams=False)
        # Then the user is returned
        assert another_normal_user.profile in resp.context["search_results"].object_list

    @pytest.mark.opensearch
    def test_search_for_old_inactive_person(self, another_normal_user):
        profile = another_normal_user.profile
        long_time_ago = datetime.datetime.now() - datetime.timedelta(days=120)
        # Given a user that has been inactive for a long time
        profile.is_active = False
        profile.became_inactive = long_time_ago
        profile.save()
        # And the search index has been updated
        call_command("update_index")
        # When I perform a search for that user
        resp = self._search("jane", teams=False)
        # Then the user is not returned
        assert (
            another_normal_user.profile
            not in resp.context["search_results"].object_list
        )
