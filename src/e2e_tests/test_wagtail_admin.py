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


@pytest.mark.e2e
def test_home_page_news_order(superuser, page: Page):
    news_home = NewsHome.objects.first()
    news_pages = NewsPageFactory.create_batch(5, parent=news_home)

    login(page, superuser)
    page.goto("/admin")
    expect(page).to_have_title(re.compile(r".*DBT Digital Workspace"))
    page.get_by_text("Home news order").click()

    # Add the news pages to define their order on the home page.
    for news_page in news_pages:
        page.get_by_text("Add Home page news order").click()
        page.get_by_text("Choose a page (News Page)").click()
        page.get_by_text(news_page.title).click()
        page.get_by_role("button", name="Save").click()

    # Visit the home page to see the news order
    page.goto("/")
    home_news_items = [
        i.inner_text() for i in page.get_by_test_id("home-news-item").all()
    ]

    # Drag the news pages to change their order.
    page.goto("/admin")
    page.get_by_text("Home news order").click()
    news_page_1 = page.get_by_role("link", name=news_pages[0].title)
    news_page_5 = page.get_by_role("link", name=news_pages[4].title)
    news_page_1.drag_to(news_page_5)

    # Visit the home page to see the updated news order
    page.goto("/")
    updated_home_news_items = [
        i.inner_text() for i in page.get_by_test_id("home-news-item").all()
    ]

    # Make sure the new order isn't the same as the old order.
    assert home_news_items != updated_home_news_items
