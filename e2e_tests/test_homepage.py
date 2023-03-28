import re

import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory


@pytest.mark.e2e
def test_homepage(page: Page):
    NewsPageFactory.create_batch(5)

    page.goto("/")
    expect(page).to_have_title(re.compile(r"Home.*"))

    page.get_by_title("News page 1")
    page.get_by_title("News page 2")
    page.get_by_title("News page 3")
    page.get_by_title("News page 4")
    page.get_by_title("News page 5")

    page.get_by_text("View all news").click()

    expect(page).to_have_title(re.compile(r"News and views.*"))
