import pytest
from django.core.management import call_command

from selenium_tests.pages.homepage import HomePage
from selenium_tests.pages.peoplefinder.team import TeamViewPage
from selenium_tests.utils import login


@pytest.mark.selenium
def test_profile(django_user_model, selenium, live_server):
    email = "test.user@example.com"

    user, _ = django_user_model.objects.get_or_create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email=email,
        legacy_sso_user_id="legacy-test-user-id",
        is_staff=True,
        is_superuser=True,
    )
    user.set_password("password")
    user.save()

    call_command("create_test_teams")
    call_command("create_user_profiles")

    login(selenium, user)

    home_page = HomePage(selenium)
    assert "Home" in selenium.title

    profile_view_page = home_page.goto_profile_view_page()
    assert "Test User" in selenium.title
    assert profile_view_page.preferred_email == email

    profile_edit_page = profile_view_page.goto_profile_edit_page()
    profile_edit_page.add_role(job_title="CEO", head_of_team=True)

    profile_view_page = profile_edit_page.save_profile()
    assert "CEO in SpaceX" in profile_view_page.roles

    TeamViewPage(selenium).goto_root_team_page()
    assert "SpaceX" in selenium.title
