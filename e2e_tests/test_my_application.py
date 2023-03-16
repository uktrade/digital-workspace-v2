import re
from playwright.sync_api import Page, expect


def test_homepage_has_Playwright_in_title_and_get_started_link_linking_to_the_intro_page(page: Page):
    page.goto("http://wagtail:8000/")

    # Expect a title "to contain" a substring.
    expect(page).to_have_title(re.compile("Home - Digital Workspace"))

    # create a locator
    news = page.get_by_role("link", name="News and views")

    # Expect an attribute "to be strictly equal" to the value.
    expect(news).to_have_attribute("href", "/news-and-views/")

    # Click the get started link.
    news.click()

    # Expects the URL to contain intro.
    expect(page).to_have_url(re.compile(".*news"))
