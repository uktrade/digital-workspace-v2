from django.db.models.query import QuerySet

from interactions.models import NetworkSubscription
from networks.models import Network
from user.models import User


def subscribe(*, network: Network, user: User) -> NetworkSubscription:
    network_subscription, _ = NetworkSubscription.objects.get_or_create(
        user=user, network=network
    )
    return network_subscription


def unsubscribe(*, network: Network, user: User) -> None:
    NetworkSubscription.objects.filter(user=user, network=network).delete()


def is_subscribed(*, network: Network, user: User) -> bool:
    return NetworkSubscription.objects.filter(user=user, network=network).exists()


def get_subscribed_networks(*, user: User) -> QuerySet[Network]:
    return Network.objects.filter(interactions_networksubscriptions__user=user)
