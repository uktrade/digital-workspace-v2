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
def news_page2():
    return NewsPage.objects.create(
        title="News 2",
        depth=1,
        path="page3",
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
def comment(comment_factory):
    return comment_factory()

# TODO: switch to kwargs for comment_factory and add back default values 
@pytest.fixture
def comment_factory(user, news_page):
    def create_comment(author=user, page=news_page, content="a comment"):
        return Comment.objects.create(author=author, page=page, content=content)

    return create_comment


@pytest.fixture
def create_comment_reaction(user, comment, news_page):
    return CommentReaction.objects.create(
        user=user, comment=comment, type=ReactionType.LIKE
    )
