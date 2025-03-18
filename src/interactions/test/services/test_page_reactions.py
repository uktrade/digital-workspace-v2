import pytest
from interactions.models import PageReaction, ReactionType
from interactions.services.page_reactions import (
    react_to_page,
    get_page_reaction_count,
    get_page_reaction_counts,
    get_user_page_reaction,
    has_user_reacted_to_page,
)

from django.test import override_settings

ALL_REACTION_TYPES = ReactionType.values


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_create(user, news_page, reaction_type):
    reaction = react_to_page(user, news_page, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_update(user, news_page, reaction_type, create_page_reaction):
    reaction = react_to_page(user, news_page, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_page_delete(user, news_page, reaction_type, create_page_reaction):
    reaction = react_to_page(user, news_page, None)
    assert reaction is None
    assert not PageReaction.objects.filter(user=user, page=news_page).exists()


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
def test_get_page_reaction_count(user, news_page, create_page_reaction):
    assert get_page_reaction_count(news_page, ReactionType.LIKE) == 1
    PageReaction.objects.filter(user=user, page=news_page).delete()
    assert get_page_reaction_count(news_page, ReactionType.LIKE) == 0


@pytest.mark.django_db
def test_get_page_reaction_count_invalid_reaction_type(
    user, news_page, create_page_reaction
):
    assert get_page_reaction_count(news_page, ReactionType.DISLIKE) == 0


@pytest.mark.django_db
def test_get_page_reaction_count_none_reaction_type(
    user, news_page, create_page_reaction
):
    assert get_page_reaction_count(news_page, None) == 1


@pytest.mark.django_db
def test_get_page_reaction_count_invalid_page(about_page):
    assert get_page_reaction_count(about_page, ReactionType.LIKE) is None


@pytest.mark.django_db
@override_settings(INACTIVE_REACTION_TYPES=[])
def test_get_page_reaction_counts(user, user2, user3, news_page):
    PageReaction.objects.create(user=user, page=news_page, type=ReactionType.LIKE)
    PageReaction.objects.create(user=user2, page=news_page, type=ReactionType.DISLIKE)
    counts = get_page_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    PageReaction.objects.create(user=user3, page=news_page, type=ReactionType.DISLIKE)
    counts = get_page_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    PageReaction.objects.filter(user=user, page=news_page).delete()
    counts = get_page_reaction_counts(news_page)
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    PageReaction.objects.filter(user=user2, page=news_page).delete()
    counts = get_page_reaction_counts(news_page)
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    PageReaction.objects.filter(user=user3, page=news_page).delete()
    counts = get_page_reaction_counts(news_page)
    assert counts.get(ReactionType.DISLIKE) == 0
    assert counts.get(ReactionType.LIKE) == 0

    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0


@pytest.mark.django_db
def test_get_page_reaction_counts_invalid_page(about_page):
    assert get_page_reaction_counts(about_page) == {}


@pytest.mark.django_db
def test_get_user_page_reaction(user, news_page, create_page_reaction):
    assert get_user_page_reaction(user, news_page) == ReactionType.LIKE


@pytest.mark.django_db
def test_get_user_page_reaction_no_page_found(user, news_page):
    assert get_user_page_reaction(user, news_page) is None


@pytest.mark.django_db
def test_has_user_not_reacted(user, news_page):
    assert has_user_reacted_to_page(user, news_page) is False


@pytest.mark.django_db
def test_has_user_reacted_to_page(user, news_page, create_page_reaction):
    assert has_user_reacted_to_page(user, news_page) is True


@pytest.mark.django_db
def test_has_user_reacted_to_page_invalid_user(user2, news_page, create_page_reaction):
    assert has_user_reacted_to_page(user2, news_page) is False
