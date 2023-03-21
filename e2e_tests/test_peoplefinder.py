# import pytest
# from django.core.management import call_command

# from peoplefinder.models import Team
# from e2e_tests.pages.homepage import HomePage
# from e2e_tests.pages.peoplefinder.team import TeamViewPage
# from e2e_tests.fixtures import superuser, login, user


# @pytest.mark.selenium
# def test_profile(superuser, user, selenium):
#     home_page = HomePage(selenium)
#     assert "Home" in selenium.title

#     profile_view_page = home_page.goto_profile_view_page()
#     assert "Test User" in selenium.title
#     assert profile_view_page.full_name == "Test User"
#     assert profile_view_page.preferred_email == superuser.email

#     profile_edit_page = profile_view_page.goto_profile_edit_page()
#     profile_edit_page.first_name = "Super"
#     profile_edit_page.manager = "John Smith"
#     profile_edit_page.add_role(job_title="CEO", head_of_team=True)

#     profile_view_page = profile_edit_page.save_profile()
#     assert profile_view_page.full_name == "Super User"
#     assert profile_view_page.manager == "John Smith"
#     assert "CEO in SpaceX" in profile_view_page.roles


# @pytest.mark.selenium
# def test_team(superuser, selenium):
#     team_view_page = TeamViewPage(selenium).goto_root_team_page()
#     assert "SpaceX" in selenium.title

#     software = Team.objects.get(name="Software")
#     team_view_page = team_view_page.goto_team_page(software)

#     assert "Software" in selenium.title

#     name = "Rocket Software"
#     abbreviation = "RS"
#     description = "The rocket software team writes code for rockets"

#     team_edit_page = team_view_page.goto_team_edit_page()
#     team_edit_page.name = name
#     team_edit_page.abbreviation = abbreviation
#     team_edit_page.description = description
#     team_view_page = team_edit_page.save_team()

#     assert team_view_page.name == name
#     assert team_view_page.abbreviation == abbreviation
#     assert team_view_page.description == description
