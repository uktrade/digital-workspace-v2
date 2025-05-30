from django.db.models import Count

from interactions.models import CommentReaction, ReactionType
from interactions.services.reactions import get_active_reactions
from news.models import Comment
from user.models import User


def react_to_comment(
    user: User, comment: Comment, reaction_type: str | None
) -> CommentReaction | None:

    if reaction_type is None:
        CommentReaction.objects.filter(user=user, comment=comment).delete()
        return None

    if reaction_type not in ReactionType.values:
        raise ValueError(f"{reaction_type} is not a valid reaction type.")

    reaction, created = CommentReaction.objects.update_or_create(
        user=user, comment=comment, defaults={"type": reaction_type}
    )

    return reaction


def get_comment_reactions(comment: Comment) -> dict | None:
    return CommentReaction.objects.filter(comment=comment).select_related("user")


def get_comment_reaction_count(
    comment: Comment, reaction_type: ReactionType | None
) -> int | None:

    reactions = CommentReaction.objects.filter(comment=comment)

    if reaction_type:
        reactions = reactions.filter(type=reaction_type)

    return reactions.count()


def get_comment_reaction_counts(comment: Comment) -> dict[str, int]:
    reaction_counts = {
        reaction_type: 0
        for reaction_type in ReactionType.values
        if reaction_type in get_active_reactions()
    }

    reactions = (
        CommentReaction.objects.filter(comment=comment)
        .values("type")
        .annotate(count=Count("id"))
    )
    reaction_counts.update(
        {
            reaction["type"]: reaction["count"]
            for reaction in reactions
            if ReactionType(reaction["type"]) in reaction_counts
        }
    )
    return reaction_counts


def get_user_comment_reaction(user: User, comment: Comment) -> ReactionType | None:
    reaction = CommentReaction.objects.filter(user=user, comment=comment).first()
    if reaction:
        return reaction.type
    return None


def has_user_reacted_to_comment(user: User, comment: Comment) -> bool:
    return CommentReaction.objects.filter(user=user, comment=comment).exists()
