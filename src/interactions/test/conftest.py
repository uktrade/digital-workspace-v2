import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from about_us.models import AboutUs
from news.models import NewsPage

from interactions.models import PageReaction, ReactionType, CommentReaction
from news.factories import CommentFactory
from peoplefinder.services.person import PersonService


@pytest.fixture
def user():
    return get_user_model().objects.create(username="test_user")


@pytest.fixture
def test_user():
    test_user_email = "test@test.com"
    test_password = "test_password"

    test_user, _ = get_user_model().objects.get_or_create(
        username="test_user",
        email=test_user_email,
    )
    test_user.set_password(test_password)
    test_user.save()
    call_command("loaddata", "countries.json")
    profile = PersonService().create_user_profile(test_user)
    test_user.profile = profile
    return test_user


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


# TODO: Update test_comment_reactions.py usage
@pytest.fixture
def comment():
    return CommentFactory.create()


@pytest.fixture
def create_page_reaction(user, news_page):
    return PageReaction.objects.create(
        user=user, page=news_page, type=ReactionType.LIKE
    )


@pytest.fixture
def create_comment_reaction(user, comment, news_page):
    return CommentReaction.objects.create(
        user=user, comment=comment, type=ReactionType.LIKE
    )
