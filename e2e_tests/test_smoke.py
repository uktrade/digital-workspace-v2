import re
import pytest

from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.usefixtures
def test_smoke(superuser, page: Page):
    page.goto("/admin")
    expect(page).to_have_title("DBT Digital Workspace")

    page.goto("/")
    expect(page).to_have_title(re.compile(r"Home.*"))

    news = page.get_by_role("link", name="News and views")
    expect(news).to_have_attribute("href", "/news-and-views/")

    news.click()
    expect(page).to_have_url(re.compile(r".*news"))
