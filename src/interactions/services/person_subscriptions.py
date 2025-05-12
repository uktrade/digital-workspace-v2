from django.db.models.query import QuerySet

from interactions.models import PersonSubscription
from peoplefinder.models import Person
from user.models import User


def subscribe(*, person: Person, user: User) -> PersonSubscription:
    team_subscription, _ = PersonSubscription.objects.get_or_create(
        user=user, person=person
    )
    return team_subscription


def unsubscribe(*, person: Person, user: User) -> None:
    PersonSubscription.objects.filter(user=user, person=person).delete()


def is_subscribed(*, person: Person, user: User) -> bool:
    return PersonSubscription.objects.filter(user=user, person=person).exists()


def get_subscribed_people(*, user: User) -> QuerySet[Person]:
    return Person.objects.filter(personsubscriptions__user=user)
