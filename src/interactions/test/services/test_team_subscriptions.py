import pytest
from interactions.services import team_subscriptions
from interactions.models import TeamSubscription
from peoplefinder.test.factories import TeamFactory



@pytest.mark.django_db
def test_subscribe(user):
    team = TeamFactory()
    assert not TeamSubscription.objects.filter(team=team, user=user).exists()

    team_subscriptions.subscribe(team=team, user=user)
    assert TeamSubscription.objects.filter(team=team, user=user).exists()


@pytest.mark.django_db
def test_unsubscribe(user):
    team = TeamFactory()
    TeamSubscription.objects.create(team=team, user=user)

    team_subscriptions.unsubscribe(team=team, user=user)
    assert not TeamSubscription.objects.filter(team=team, user=user).exists()


@pytest.mark.django_db
def test_is_subscribed(user):
    team = TeamFactory()

    assert not team_subscriptions.is_subscribed(team=team, user=user)

    TeamSubscription.objects.create(team=team, user=user)
    assert team_subscriptions.is_subscribed(team=team, user=user)


@pytest.mark.django_db
def test_get_subscribed_teams(user):
    team1 = TeamFactory()
    team2 = TeamFactory()
    team3 = TeamFactory()

    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 not in subscribed_teams
    assert team2 not in subscribed_teams
    assert team3 not in subscribed_teams

    team_subscriptions.subscribe(team=team1, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 in subscribed_teams
    assert team2 not in subscribed_teams
    assert team3 not in subscribed_teams

    team_subscriptions.subscribe(team=team2, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 in subscribed_teams
    assert team2 in subscribed_teams
    assert team3 not in subscribed_teams

    team_subscriptions.subscribe(team=team3, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 in subscribed_teams
    assert team2 in subscribed_teams
    assert team3 in subscribed_teams

    team_subscriptions.unsubscribe(team=team2, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 in subscribed_teams
    assert team2 not in subscribed_teams
    assert team3 in subscribed_teams

    team_subscriptions.unsubscribe(team=team3, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 in subscribed_teams
    assert team2 not in subscribed_teams
    assert team3 not in subscribed_teams

    team_subscriptions.unsubscribe(team=team1, user=user)
    subscribed_teams = list(team_subscriptions.get_subscribed_teams(user=user))
    assert team1 not in subscribed_teams
    assert team2 not in subscribed_teams
    assert team3 not in subscribed_teams
