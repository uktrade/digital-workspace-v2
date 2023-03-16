# import pytest
# from django.core.management import call_command

# from selenium_tests.pages.homepage import HomePage
# from selenium_tests.utils import login


# @pytest.mark.selenium
# def test_smoke(django_user_model, selenium, live_server):
#     user, _ = django_user_model.objects.get_or_create(
#         username="testuser",
#         first_name="Test",
#         last_name="User",
#         email="test.user@example.com",
#         legacy_sso_user_id="legacy-test-user-id",
#         is_staff=True,
#         is_superuser=True,
#     )
#     user.set_password("password")
#     user.save()

#     call_command("create_test_teams")
#     call_command("create_user_profiles")

#     login(selenium, user)

#     home_page = HomePage(selenium)
#     assert "Home" in selenium.title

#     wagtail_admin_page = home_page.goto_wagtail_admin_page()
#     assert "DBT Digital Workspace" in selenium.title

#     home_page = wagtail_admin_page.get_home_page()
#     assert "Home" in selenium.title
