import re

import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory
from news.models import NewsHome

from .pages.homepage import HomePage
from .utils import login


@pytest.mark.e2e
def test_bookmark_a_news_page(superuser, user, page: Page):
    news_home_page = NewsHome.objects.get()
    news_page = NewsPageFactory.create(parent=news_home_page)

    login(page, user)
    page.goto("/")
    home_page = HomePage(page)

    # Check the user has no bookmarks to begin with
    assert 0 == len(home_page.bookmarks)

    # Go to the news page and bookmark it
    page.goto(news_page.get_url())
    page.get_by_test_id("bookmark-this-page").click()

    # Check to see if there is a new bookmark on the homepage
    page.goto("/")
    home_page = HomePage(page)
    assert 1 == len(home_page.bookmarks)

    # Click the bookmark and make sure it goes to the correct page:
    first_bookmark = home_page.bookmarks[0]
    first_bookmark.click()
    expect(page).to_have_title(re.compile(rf"{news_page.title}.*"))
