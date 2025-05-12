from django.db.models.query import QuerySet

from interactions.models import TeamSubscription
from peoplefinder.models import Team
from user.models import User


def subscribe(*, team: Team, user: User) -> TeamSubscription:
    team_subscription, _ = TeamSubscription.objects.get_or_create(user=user, team=team)
    return team_subscription


def unsubscribe(*, team: Team, user: User) -> None:
    TeamSubscription.objects.filter(user=user, team=team).delete()


def is_subscribed(*, team: Team, user: User) -> bool:
    return TeamSubscription.objects.filter(user=user, team=team).exists()


def get_subscribed_teams(*, user: User) -> QuerySet[Team]:
    return Team.objects.filter(interactions_teamsubscriptions__user=user)
