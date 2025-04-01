import re

import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory

from .utils import login


@pytest.mark.e2e
def test_homepage(superuser, user, page: Page):
    news_pages = NewsPageFactory.create_batch(5)

    login(page, user)
    page.goto("/")
    expect(page).to_have_title(re.compile(r"Home.*"))

    for news_page in news_pages:
        page.get_by_title(news_page.title)

    page.get_by_role("link", name="View all news").click()
