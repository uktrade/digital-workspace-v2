
import pytest
from playwright.sync_api import Page, expect

from .utils import login


@pytest.mark.e2e
def test_navigation(superuser, user, page: Page):
    login(page, user)
    page.goto("/")

    news = page.get_by_test_id("main-menu-news")
    expect(news).to_have_attribute("href", "/news-and-views/")
    news.click()

    page.get_by_role("link", name="Working at DBT").click()
    page.get_by_role("heading", name="Working at DBT").click()

    page.get_by_role("link", name="About us").click()
    page.get_by_role("heading", name="About us").click()

    page.get_by_role("link", name="Tools").click()
    page.get_by_role("heading", name="Tools").click()
