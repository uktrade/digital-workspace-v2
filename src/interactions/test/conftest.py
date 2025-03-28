import pytest
from django.contrib.auth import get_user_model

from about_us.models import AboutUs
from news.models import NewsPage, Comment

from interactions.models import PageReaction, ReactionType, CommentReaction


@pytest.fixture
def user():
    return get_user_model().objects.create(username="test_user")


@pytest.fixture
def user2():
    return get_user_model().objects.create(username="test_user2")


@pytest.fixture
def user3():
    return get_user_model().objects.create(username="test_user3")


@pytest.fixture
def news_page():
    return NewsPage.objects.create(
        title="News",
        depth=1,
        path="page2",
    )


@pytest.fixture
def about_page():
    return AboutUs.objects.create(
        title="About Us",
        depth=4,
        path="page1",
    )


@pytest.fixture
def create_page_reaction(user, news_page):
    return PageReaction.objects.create(
        user=user, page=news_page, type=ReactionType.LIKE
    )


@pytest.fixture
def comment(user, news_page):
    return Comment.objects.create(author=user, page=news_page, content="a comment")


@pytest.fixture
def create_comment_reaction(user, comment, news_page):
    return CommentReaction.objects.create(
        user=user, comment=comment, type=ReactionType.LIKE
    )
