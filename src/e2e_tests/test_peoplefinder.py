import re

import pytest
from playwright.sync_api import Page, expect

from e2e_tests.pages.homepage import HomePage
from e2e_tests.pages.peoplefinder.team import TeamViewPage
from peoplefinder.models import Team

from .utils import login


@pytest.mark.e2e
def test_profile(superuser, user, page: Page):
    login(page, user)
    page.goto("/")
    home_page = HomePage(page)

    # Profile page
    profile_view_page = home_page.goto_profile_view_page()
    expect(profile_view_page.page).to_have_title(re.compile(r"J Smith.*"))
    assert profile_view_page.full_name == "J Smith"
    assert profile_view_page.preferred_email == user.email

    # Profile edit page
    profile_edit_page = profile_view_page.goto_profile_edit_page()
    assert profile_edit_page.first_name == "John"
    profile_edit_team_page = profile_edit_page.goto_profile_edit_team_page()
    assert profile_edit_team_page.manager == "Super User"
    profile_edit_team_page.add_role(job_title="CEO", head_of_team=True)
    profile_edit_team_page.save_profile()

    # Updated profile page
    profile_view_page = profile_edit_page.goto_profile_view_page()
    assert profile_view_page.full_name == "J Smith"
    assert profile_view_page.manager == "Super User"
    assert "CEO in SpaceX" in profile_view_page.roles


@pytest.mark.e2e
def test_team(superuser, user, page: Page):
    login(page, superuser)

    team_view_page = TeamViewPage(page).goto_root_team_page()
    expect(team_view_page.page).to_have_title(re.compile(r"SpaceX.*"))

    software = Team.objects.get(name="Software")
    team_view_page = team_view_page.goto_team_page(software)
    expect(team_view_page.page).to_have_title(re.compile(r"Software.*"))

    name = "Rocket Software"
    abbreviation = "RS"
    description = "The rocket software team writes code for rockets"

    team_edit_page = team_view_page.goto_team_edit_page()
    team_edit_page.name = name
    team_edit_page.abbreviation = abbreviation
    team_edit_page.description = description
    team_view_page = team_edit_page.save_team()

    assert team_view_page.name == name
    assert team_view_page.abbreviation == abbreviation
    assert team_view_page.description == description
