import re

import pytest
from django.core.management import call_command
from playwright.sync_api import Page, expect

from .utils import login


@pytest.mark.e2e
def test_smoke(django_user_model, page: Page, live_server):
    user, _ = django_user_model.objects.get_or_create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
        legacy_sso_user_id="legacy-test-user-id",
        is_staff=True,
        is_superuser=True,
    )
    user.set_password("password")
    user.save()

    call_command("create_test_teams")
    call_command("create_user_profiles")

    login(page, user)

    page.goto("/")
    expect(page).to_have_title(re.compile("Home"))

    page.goto("/admin")
    expect(page).to_have_title(re.compile("DBT Digital Workspace"))

    page.goto("/")
    expect(page).to_have_title(re.compile("Home"))

    news = page.get_by_role("link", name="News")
    expect(news).to_have_attribute("href", "/news-and-views/")
    news.click()
    expect(page).to_have_url(re.compile(".*news"))
