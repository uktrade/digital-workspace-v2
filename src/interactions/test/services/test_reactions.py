import pytest
from django.contrib.auth import get_user_model

from about_us.models import AboutUs
from interactions.models import Reaction, ReactionType
from interactions.services.reactions import (
    manage_reaction,
)
from news.models import NewsPage


@pytest.fixture
def user():
    return get_user_model().objects.create(username="another_user")


@pytest.fixture
def news_page():
    return NewsPage.objects.create(
        title="News",
        slug="news-and-views",
        depth=1,
        path="page2",
        search_title="Page Title",
        description="Description",
        search_headings="Heading 2",
    )


@pytest.fixture
def about_page():
    return AboutUs.objects.create(
        title="About Us",
        slug="about-us",
        depth=4,
        path="page1",
        search_title="Page Title",
        description="Description",
    )


@pytest.mark.django_db
def test_manage_reaction_create(user, news_page):
    manage_reaction(user, news_page, ReactionType.LIKE)
    reaction = Reaction.objects.get(user=user, page=news_page)
    assert reaction.type == ReactionType.LIKE


@pytest.mark.django_db
def test_manage_reaction_update(user, news_page):
    Reaction.objects.create(user=user, page=news_page, type=ReactionType.LIKE)
    manage_reaction(user, news_page, ReactionType.DISLIKE)
    reaction = Reaction.objects.get(user=user, page=news_page)
    assert reaction.type == ReactionType.DISLIKE


@pytest.mark.django_db
# Test for user deselects reaction
def test_manage_reaction_delete(user, news_page):
    Reaction.objects.create(user=user, page=news_page, type=ReactionType.LIKE)
    manage_reaction(user, news_page, None)
    assert not Reaction.objects.filter(user=user, page=news_page).exists()


@pytest.mark.django_db
def test_manage_reaction_invalid_page(user, about_page):
    with pytest.raises(ValueError):
        manage_reaction(user, about_page, ReactionType.LIKE)
