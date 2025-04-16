from django.conf import settings

from interactions.models import ReactionType


def get_active_reactions() -> list[ReactionType]:
    inactive_reaction_types = [
        ReactionType(rt) for rt in settings.INACTIVE_REACTION_TYPES
    ]
    return [rt for rt in ReactionType if rt not in inactive_reaction_types]
