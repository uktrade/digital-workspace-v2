import re

import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory
from news.models import NewsHome

from .utils import login


@pytest.mark.e2e
def test_add_news_page(superuser, page: Page):
    news_home = NewsHome.objects.first()
    NewsPageFactory.create_batch(5, parent=news_home)

    login(page, superuser)
    page.goto("/admin")
    expect(page).to_have_title(re.compile(r".*DBT Digital Workspace"))

    page.get_by_role("button", name="Pages").click()
    page.get_by_role("link", name="Home", exact=True).click()
    page.get_by_role("link", name="Explore child pages of 'News'").click()
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Add child page").click()

    # Create a news page.
    page.get_by_role("textbox", name="title").fill("Test news page")
    page.get_by_role("button", name="Insert a block").click()
    page.get_by_placeholder("Search options…").fill("Heading 2")
    page.keyboard.press("Enter")
    page.locator("#body-0-value").fill("Test news page heading")

    # TODO: The choose an image modal doesn't seem to be appearing.
    # page.get_by_role("button", name="Choose an image").click()
    # page.locator(".image-choice").nth(0).click()

    # Save draft
    page.get_by_role("button", name="Save draft").click()

    # Publish
    page.locator("nav.footer__container .w-dropdown--dropdown-button").click()
    page.get_by_role("button", name="Publish").click()

    # Check the page is visible in the admin.
    page.get_by_text("Test news page")
