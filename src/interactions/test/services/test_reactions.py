import pytest
from django.contrib.auth import get_user_model

from about_us.models import AboutUs
from interactions.models import Reaction, ReactionType
from interactions.services.reactions import (
    manage_reaction,
)
from news.models import NewsPage

ALL_REACTION_TYPES = ReactionType.values


@pytest.fixture
def user():
    return get_user_model().objects.create(username="test_user")


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


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_manage_reaction_create(user, news_page, reaction_type):
    manage_reaction(user, news_page, reaction_type)
    assert_reaction_type(user, news_page, reaction_type)


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_manage_reaction_update(user, news_page, reaction_type):
    create_reaction(user, news_page, ReactionType.LIKE)
    manage_reaction(user, news_page, reaction_type)
    assert_reaction_type(user, news_page, reaction_type)


def assert_reaction_type(user, page, expected_type):
    reaction = Reaction.objects.get(user=user, page=page)
    assert reaction.type == expected_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
# Test for user deselects reaction
def test_manage_reaction_delete(user, news_page, reaction_type):
    create_reaction(user, news_page, reaction_type)
    manage_reaction(user, news_page, None)
    assert not Reaction.objects.filter(user=user, page=news_page).exists()


def create_reaction(user, page, reaction_type):
    return Reaction.objects.create(user=user, page=page, type=reaction_type)


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_manage_reaction_invalid_page(user, about_page, reaction_type):
    with pytest.raises(ValueError):
        manage_reaction(user, about_page, reaction_type)
