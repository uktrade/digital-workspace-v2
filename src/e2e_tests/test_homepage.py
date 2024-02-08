import re

import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory

from .utils import login


@pytest.mark.e2e
def test_homepage(superuser, user, page: Page):
    NewsPageFactory.create_batch(5)

    login(page, user)
    page.goto("/")
    expect(page).to_have_title(re.compile(r"Home.*"))

    page.get_by_title("News page 1")
    page.get_by_title("News page 2")
    page.get_by_title("News page 3")
    page.get_by_title("News page 4")
    page.get_by_title("News page 5")

    page.get_by_text("Quick links").click()
    page.get_by_role("heading", name="Popular on Digital Workspace").click()
    page.get_by_role("heading", name="How do I?").click()
    page.get_by_role("heading", name="DBT news from GOV.UK").click()

    news = page.get_by_test_id("main-menu-news")
    expect(news).to_have_attribute("href", "/news-and-views/")
    news.click()
    page.get_by_role("heading", name="All news categories").click()

    page.get_by_role("link", name="Working at DBT").click()
    page.get_by_role("heading", name="Working at DBT").click()

    page.get_by_role("link", name="About us").click()
    page.get_by_role("heading", name="About us").click()

    page.get_by_role("link", name="Tools").click()
    page.get_by_role("heading", name="Tools").click()
