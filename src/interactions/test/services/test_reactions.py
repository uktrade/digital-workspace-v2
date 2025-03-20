from interactions.models import ReactionType
from interactions.services.comment_reactions import get_active_reactions

from django.test import override_settings


@override_settings(INACTIVE_REACTION_TYPES=[])
def test_get_active_reactions_default():
    response = get_active_reactions()
    assert ReactionType.CELEBRATE in response
    assert ReactionType.LIKE in response
    assert ReactionType.LOVE in response
    assert ReactionType.DISLIKE in response
    assert ReactionType.UNHAPPY in response


@override_settings(INACTIVE_REACTION_TYPES=["unhappy", "like"])
def test_get_active_reactions_settings():
    response = get_active_reactions()
    assert ReactionType.CELEBRATE in response
    assert ReactionType.LIKE not in response
    assert ReactionType.LOVE in response
    assert ReactionType.DISLIKE in response
    assert ReactionType.UNHAPPY not in response
