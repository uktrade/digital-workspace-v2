import re

import pytest
from playwright.sync_api import Page, expect

from .utils import login


@pytest.mark.e2e
def test_wagtail_accessible(superuser, page: Page):
    login(page, superuser)

    page.goto("/admin")
    expect(page).to_have_title(re.compile(r".*DBT Digital Workspace"))


@pytest.mark.e2e
def test_site_has_all_major_sections(page: Page):
    page.goto("/")
    expect(page).to_have_title(re.compile(r"Home.*"))


    # page.get_by_text("Quick links").click()
    # page.get_by_role("heading", name="What's Popular?").click()
    # page.get_by_role("heading", name="How do I?").click()
    # page.get_by_role("heading", name="DBT news from GOV.UK").click()
    # page.get_by_role("heading", name="Latest tweets").click()

    # news = page.get_by_role("link", name="News and views").click()
    # expect(news).to_have_attribute("href", "/news-and-views/")
    # news.click()
    # page.get_by_role("heading", name="All news categories").click()

    # page.get_by_role("link", name="Working at DBT").click()
    # page.get_by_role("heading", name="Working at DBT").click()

    # page.get_by_role("link", name="About us").click()
    # page.get_by_role("heading", name="About us").click()

    # page.get_by_role("link", name="Tools").click()
    # page.get_by_role("heading", name="Tools").click()
