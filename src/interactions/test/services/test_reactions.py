import pytest

from interactions.models import Reaction, ReactionType
from interactions.services.reactions import (
    react_to_page,
)

ALL_REACTION_TYPES = ReactionType.values


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_create(user, news_page, reaction_type):
    reaction = react_to_page(user, news_page, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_update(user, news_page, reaction_type, create_reaction):
    reaction = react_to_page(user, news_page, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_delete(user, news_page, reaction_type, create_reaction):
    reaction = react_to_page(user, news_page, None)
    assert reaction is None
    assert not Reaction.objects.filter(user=user, page=news_page).exists()


@pytest.mark.django_db
def test_react_to_page_invalid_reaction_type(user, news_page):
    with pytest.raises(ValueError):
        react_to_page(user, news_page, "heart_eyes")


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_invalid_page(user, about_page, reaction_type):
    with pytest.raises(ValueError):
        react_to_page(user, about_page, reaction_type)
