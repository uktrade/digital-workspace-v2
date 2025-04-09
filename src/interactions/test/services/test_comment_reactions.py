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

from news.factories import CommentFactory
from peoplefinder.test.factories import UserWithPersonFactory

ALL_REACTION_TYPES = ReactionType.values


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_create(reaction_type):
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    reaction = react_to_comment(test_user1, comment, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_update(reaction_type):
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=test_user1, comment=comment, type=reaction_type
    )
    reaction = react_to_comment(test_user1, comment, reaction_type)
    assert reaction.type == reaction_type


@pytest.mark.django_db
@pytest.mark.parametrize("reaction_type", ALL_REACTION_TYPES)
def test_react_to_comment_delete(reaction_type):
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=test_user1, comment=comment, type=reaction_type
    )
    reaction = react_to_comment(test_user1, comment, None)
    assert reaction is None
    assert not CommentReaction.objects.filter(user=test_user1, comment=comment).exists()


@pytest.mark.django_db
def test_react_to_comment_invalid_reaction_type():
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    with pytest.raises(ValueError):
        react_to_comment(test_user1, comment, "heart_eyes")


@pytest.mark.django_db
def test_get_comment_reaction_count():
    comment = CommentFactory()
    reaction = CommentReaction.objects.create(
        user=UserWithPersonFactory(), comment=comment, type=ReactionType.LIKE
    )
    assert get_comment_reaction_count(comment, ReactionType.LIKE) == 1
    reaction.delete()
    assert get_comment_reaction_count(comment, ReactionType.LIKE) == 0


@pytest.mark.django_db
def test_get_comment_reaction_count_invalid_reaction_type():
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=UserWithPersonFactory(), comment=comment, type=ReactionType.LIKE
    )
    assert get_comment_reaction_count(comment, ReactionType.DISLIKE) == 0


@pytest.mark.django_db
def test_get_comment_reaction_count_none_reaction_type():
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=UserWithPersonFactory(), comment=comment, type=ReactionType.LIKE
    )
    assert get_comment_reaction_count(comment, None) == 1


@pytest.mark.django_db
@override_settings(INACTIVE_REACTION_TYPES=[])
def test_get_comment_reaction_counts():
    test_user1 = UserWithPersonFactory()
    test_user2 = UserWithPersonFactory()
    test_user3 = UserWithPersonFactory()
    test_comment = CommentFactory()

    CommentReaction.objects.create(user=test_user1, comment=test_comment, type=ReactionType.LIKE)
    CommentReaction.objects.create(
        user=test_user2, comment=test_comment, type=ReactionType.DISLIKE
    )
    counts = get_comment_reaction_counts(test_comment)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.create(
        user=test_user3, comment=test_comment, type=ReactionType.DISLIKE
    )
    counts = get_comment_reaction_counts(test_comment)
    assert counts.get(ReactionType.LIKE) == 1
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=test_user1, comment=test_comment).delete()
    counts = get_comment_reaction_counts(test_comment)
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.DISLIKE) == 2
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=test_user2, comment=test_comment).delete()
    counts = get_comment_reaction_counts(test_comment)
    assert counts.get(ReactionType.DISLIKE) == 1
    assert counts.get(ReactionType.LIKE) == 0
    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0

    CommentReaction.objects.filter(user=test_user3, comment=test_comment).delete()
    counts = get_comment_reaction_counts(test_comment)
    assert counts.get(ReactionType.DISLIKE) == 0
    assert counts.get(ReactionType.LIKE) == 0

    assert counts.get(ReactionType.CELEBRATE) == 0
    assert counts.get(ReactionType.UNHAPPY) == 0
    assert counts.get(ReactionType.LOVE) == 0


@pytest.mark.django_db
def test_get_user_comment_reaction():
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=test_user1, comment=comment, type=ReactionType.LIKE
    )
    assert get_user_comment_reaction(test_user1, comment) == ReactionType.LIKE


@pytest.mark.django_db
def test_get_user_comment_reaction_no_comment_found():
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    assert get_user_comment_reaction(test_user1, comment) is None


@pytest.mark.django_db
def test_has_user_not_reacted():
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    assert has_user_reacted_to_comment(test_user1, comment) is False


@pytest.mark.django_db
def test_has_user_reacted_to_comment():
    test_user1 = UserWithPersonFactory()
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=test_user1, comment=comment, type=ReactionType.LIKE
    )
    assert has_user_reacted_to_comment(test_user1, comment) is True


@pytest.mark.django_db
def test_has_user_reacted_to_comment_invalid_user():
    test_user1 = UserWithPersonFactory()
    test_user2 = UserWithPersonFactory()
    comment = CommentFactory()
    CommentReaction.objects.create(
        user=test_user1, comment=comment, type=ReactionType.LIKE
    )
    assert has_user_reacted_to_comment(test_user2, comment) is False
