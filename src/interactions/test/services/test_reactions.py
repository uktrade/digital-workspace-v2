import pytest

from interactions.models import Reaction, ReactionType
from interactions.services.reactions import (
    react_to_page,
    get_reaction_count,
    get_reaction_counts,
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


@pytest.mark.django_db
def test_get_reaction_count(user, news_page, create_reaction):
    assert get_reaction_count(news_page) == 1
    Reaction.objects.filter(user=user, page=news_page).delete()
    assert get_reaction_count(news_page) == 0


@pytest.mark.django_db
def test_get_reaction_count_invalid_page(about_page):
    assert get_reaction_count(about_page) is None


@pytest.mark.django_db
def test_get_reaction_counts(user, user2, user3, news_page):
    Reaction.objects.create(user=user, page=news_page, type=ReactionType.LIKE)
    Reaction.objects.create(user=user2, page=news_page, type=ReactionType.DISLIKE)
    counts = get_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 1
    assert_counts(counts)

    Reaction.objects.create(user=user3, page=news_page, type=ReactionType.DISLIKE)
    counts = get_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 2
    assert_counts(counts)

    Reaction.objects.filter(user=user, page=news_page).delete()
    counts = get_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.DISLIKE) == 2
    assert_counts(counts)

    Reaction.objects.filter(user=user2, page=news_page).delete()
    counts = get_reaction_counts(news_page)
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.LIKE) == 0
    assert_counts(counts)

    Reaction.objects.filter(user=user3, page=news_page).delete()
    counts = get_reaction_counts(news_page)
    assert counts.get(ReactionType.DISLIKE) == 0
    assert counts.get(ReactionType.LIKE) == 0
    assert_counts(counts)


def assert_counts(counts):
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0


@pytest.mark.django_db
def test_get_reaction_counts_invalid_page(user, user2, about_page):
    assert get_reaction_counts(about_page) == {}
