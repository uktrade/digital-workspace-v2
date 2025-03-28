import pytest
from playwright.sync_api import Page, expect

from news.factories import NewsPageFactory
from news.models import NewsHome

from .utils import login


@pytest.mark.e2e
def test_give_feedback(superuser, user, page: Page):
    news_home_page = NewsHome.objects.get()
    news_page = NewsPageFactory.create(parent=news_home_page)

    login(page, user)

    # Go to the news page and click the "Give feedback" button
    page.goto(news_page.get_url())
    page.get_by_test_id("give-feedback-button").click()

    # Check to see that the browser's focus is the feedback form
    expect(page.locator("textarea[name='trying_to']")).to_be_focused()
