import pytest
from interactions.services import person_subscriptions
from interactions.models import PersonSubscription
from peoplefinder.test.factories import PersonFactory


@pytest.mark.django_db
def test_subscribe(user):
    person = PersonFactory()
    assert not PersonSubscription.objects.filter(person=person, user=user).exists()

    person_subscriptions.subscribe(person=person, user=user)
    assert PersonSubscription.objects.filter(person=person, user=user).exists()


@pytest.mark.django_db
def test_unsubscribe(user):
    person = PersonFactory()
    PersonSubscription.objects.create(person=person, user=user)

    person_subscriptions.unsubscribe(person=person, user=user)
    assert not PersonSubscription.objects.filter(person=person, user=user).exists()


@pytest.mark.django_db
def test_is_subscribed(user):
    person = PersonFactory()

    assert not person_subscriptions.is_subscribed(person=person, user=user)

    PersonSubscription.objects.create(person=person, user=user)
    assert person_subscriptions.is_subscribed(person=person, user=user)


@pytest.mark.django_db
def test_get_subscribed_people(user):
    person1 = PersonFactory()
    person2 = PersonFactory()
    person3 = PersonFactory()

    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 not in subscribed_people
    assert person2 not in subscribed_people
    assert person3 not in subscribed_people

    person_subscriptions.subscribe(person=person1, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 in subscribed_people
    assert person2 not in subscribed_people
    assert person3 not in subscribed_people

    person_subscriptions.subscribe(person=person2, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 in subscribed_people
    assert person2 in subscribed_people
    assert person3 not in subscribed_people

    person_subscriptions.subscribe(person=person3, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 in subscribed_people
    assert person2 in subscribed_people
    assert person3 in subscribed_people

    person_subscriptions.unsubscribe(person=person2, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 in subscribed_people
    assert person2 not in subscribed_people
    assert person3 in subscribed_people

    person_subscriptions.unsubscribe(person=person3, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 in subscribed_people
    assert person2 not in subscribed_people
    assert person3 not in subscribed_people

    person_subscriptions.unsubscribe(person=person1, user=user)
    subscribed_people = list(person_subscriptions.get_subscribed_people(user=user))
    assert person1 not in subscribed_people
    assert person2 not in subscribed_people
    assert person3 not in subscribed_people
