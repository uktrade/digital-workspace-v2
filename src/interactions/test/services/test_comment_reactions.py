import pytest

from interactions.models import CommentReaction, ReactionType
from interactions.services.comment_reactions import (
    react_to_comment,
    get_comment_reaction_count,
    get_comment_reaction_counts,
    get_user_comment_reaction,
    has_user_reacted_to_comment,
)
from django.test import override_settings

ALL_REACTION_TYPES = ReactionType.values


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_create(user, comment, reaction_type):
    reaction = react_to_comment(user, comment, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_update(user, comment, reaction_type, create_comment_reaction):
    reaction = react_to_comment(user, comment, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_delete(user, comment, reaction_type, create_comment_reaction):
    reaction = react_to_comment(user, comment, None)
    assert reaction is None
    assert not CommentReaction.objects.filter(user=user, comment=comment).exists()


@pytest.mark.django_db
def test_react_to_comment_invalid_reaction_type(user, comment):
    with pytest.raises(ValueError):
        react_to_comment(user, comment, "heart_eyes")


@pytest.mark.django_db
def test_get_comment_reaction_count(user, comment, create_comment_reaction):
    assert get_comment_reaction_count(comment, ReactionType.LIKE) == 1
    CommentReaction.objects.filter(user=user, comment=comment).delete()
    assert get_comment_reaction_count(comment, ReactionType.LIKE) == 0


@pytest.mark.django_db
def test_get_comment_reaction_count_invalid_reaction_type(
    user, comment, create_comment_reaction
):
    assert get_comment_reaction_count(comment, ReactionType.DISLIKE) == 0


@pytest.mark.django_db
def test_get_comment_reaction_count_none_reaction_type(
    user, comment, create_comment_reaction
):
    assert get_comment_reaction_count(comment, None) == 1


@pytest.mark.django_db
@override_settings(INACTIVE_REACTION_TYPES=[])
def test_get_comment_reaction_counts(user, user2, user3, comment):
    CommentReaction.objects.create(user=user, comment=comment, type=ReactionType.LIKE)
    CommentReaction.objects.create(
        user=user2, comment=comment, type=ReactionType.DISLIKE
    )
    counts = get_comment_reaction_counts(comment)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.create(
        user=user3, comment=comment, type=ReactionType.DISLIKE
    )
    counts = get_comment_reaction_counts(comment)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=user, comment=comment).delete()
    counts = get_comment_reaction_counts(comment)
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=user2, comment=comment).delete()
    counts = get_comment_reaction_counts(comment)
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=user3, comment=comment).delete()
    counts = get_comment_reaction_counts(comment)
    assert counts.get(ReactionType.DISLIKE) == 0
    assert counts.get(ReactionType.LIKE) == 0

    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0


@pytest.mark.django_db
def test_get_user_comment_reaction(user, comment, create_comment_reaction):
    assert get_user_comment_reaction(user, comment) == ReactionType.LIKE


@pytest.mark.django_db
def test_get_user_comment_reaction_no_comment_found(user, comment):
    assert get_user_comment_reaction(user, comment) is None


@pytest.mark.django_db
def test_has_user_not_reacted(user, comment):
    assert has_user_reacted_to_comment(user, comment) is False


@pytest.mark.django_db
def test_has_user_reacted_to_comment(user, comment, create_comment_reaction):
    assert has_user_reacted_to_comment(user, comment) is True


@pytest.mark.django_db
def test_has_user_reacted_to_comment_invalid_user(
    user2, comment, create_comment_reaction
):
    assert has_user_reacted_to_comment(user2, comment) is False
