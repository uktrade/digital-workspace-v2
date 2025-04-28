import pytest
from interactions.services import tag_subscriptions
from interactions.models import TagSubscription

from core.models.tags import Tag


@pytest.mark.django_db
def test_subscribe(user):
    tag = Tag.objects.create(
        name="Test tag 1",
        slug="test-tag-1",
    )
    assert not TagSubscription.objects.filter(tag=tag, user=user).exists()

    tag_subscriptions.subscribe(tag=tag, user=user)
    assert TagSubscription.objects.filter(tag=tag, user=user).exists()


@pytest.mark.django_db
def test_unsubscribe(user):
    tag = Tag.objects.create(
        name="Test tag 1",
        slug="test-tag-1",
    )
    TagSubscription.objects.create(tag=tag, user=user)

    tag_subscriptions.unsubscribe(tag=tag, user=user)
    assert not TagSubscription.objects.filter(tag=tag, user=user).exists()


@pytest.mark.django_db
def test_is_subscribed(user):
    tag = Tag.objects.create(
        name="Test tag 1",
        slug="test-tag-1",
    )

    assert not tag_subscriptions.is_subscribed(tag=tag, user=user)

    TagSubscription.objects.create(tag=tag, user=user)
    assert tag_subscriptions.is_subscribed(tag=tag, user=user)


@pytest.mark.django_db
def test_get_subscribed_tags(user):
    tag1 = Tag.objects.create(
        name="Test tag 1",
        slug="test-tag-1",
    )
    tag2 = Tag.objects.create(
        name="Test tag 2",
        slug="test-tag-2",
    )
    tag3 = Tag.objects.create(
        name="Test tag 3",
        slug="test-tag-3",
    )

    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 not in subscribed_tags
    assert tag2 not in subscribed_tags
    assert tag3 not in subscribed_tags

    tag_subscriptions.subscribe(tag=tag1, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 in subscribed_tags
    assert tag2 not in subscribed_tags
    assert tag3 not in subscribed_tags

    tag_subscriptions.subscribe(tag=tag2, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 in subscribed_tags
    assert tag2 in subscribed_tags
    assert tag3 not in subscribed_tags

    tag_subscriptions.subscribe(tag=tag3, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 in subscribed_tags
    assert tag2 in subscribed_tags
    assert tag3 in subscribed_tags

    tag_subscriptions.unsubscribe(tag=tag2, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 in subscribed_tags
    assert tag2 not in subscribed_tags
    assert tag3 in subscribed_tags

    tag_subscriptions.unsubscribe(tag=tag3, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 in subscribed_tags
    assert tag2 not in subscribed_tags
    assert tag3 not in subscribed_tags

    tag_subscriptions.unsubscribe(tag=tag1, user=user)
    subscribed_tags = list(tag_subscriptions.get_subscribed_tags(user=user))
    assert tag1 not in subscribed_tags
    assert tag2 not in subscribed_tags
    assert tag3 not in subscribed_tags
