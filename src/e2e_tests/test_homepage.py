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
    page.get_by_role("link", name="View all news").click()
