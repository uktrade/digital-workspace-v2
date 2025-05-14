import pytest
from interactions.services import network_subscriptions
from interactions.models import NetworkSubscription
from networks.factories import NetworkFactory


@pytest.mark.django_db
def test_subscribe(user):
    network = NetworkFactory()
    assert not NetworkSubscription.objects.filter(network=network, user=user).exists()

    network_subscriptions.subscribe(network=network, user=user)
    assert NetworkSubscription.objects.filter(network=network, user=user).exists()


@pytest.mark.django_db
def test_unsubscribe(user):
    network = NetworkFactory()
    NetworkSubscription.objects.create(network=network, user=user)

    network_subscriptions.unsubscribe(network=network, user=user)
    assert not NetworkSubscription.objects.filter(network=network, user=user).exists()


@pytest.mark.django_db
def test_is_subscribed(user):
    network = NetworkFactory()

    assert not network_subscriptions.is_subscribed(network=network, user=user)

    NetworkSubscription.objects.create(network=network, user=user)
    assert network_subscriptions.is_subscribed(network=network, user=user)


@pytest.mark.django_db
def test_get_subscribed_networks(user):
    network1 = NetworkFactory()
    network2 = NetworkFactory()
    network3 = NetworkFactory()

    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 not in subscribed_networks
    assert network2 not in subscribed_networks
    assert network3 not in subscribed_networks

    network_subscriptions.subscribe(network=network1, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 in subscribed_networks
    assert network2 not in subscribed_networks
    assert network3 not in subscribed_networks

    network_subscriptions.subscribe(network=network2, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 in subscribed_networks
    assert network2 in subscribed_networks
    assert network3 not in subscribed_networks

    network_subscriptions.subscribe(network=network3, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 in subscribed_networks
    assert network2 in subscribed_networks
    assert network3 in subscribed_networks

    network_subscriptions.unsubscribe(network=network2, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 in subscribed_networks
    assert network2 not in subscribed_networks
    assert network3 in subscribed_networks

    network_subscriptions.unsubscribe(network=network3, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 in subscribed_networks
    assert network2 not in subscribed_networks
    assert network3 not in subscribed_networks

    network_subscriptions.unsubscribe(network=network1, user=user)
    subscribed_networks = list(network_subscriptions.get_subscribed_networks(user=user))
    assert network1 not in subscribed_networks
    assert network2 not in subscribed_networks
    assert network3 not in subscribed_networks
