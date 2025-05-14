import pytest
from django.test.client import Client
from django.urls import reverse
from core.factories import TagFactory
from interactions.models import TagSubscription
from interactions.services import tag_subscriptions

pytestmark = pytest.mark.django_db


def test_subscribe(user):
    tag = TagFactory()
    client = Client()
    client.force_login(user)
    url = reverse("interactions:subscribe-to-tag", args=[tag.pk])

    assert not TagSubscription.objects.filter(user=user, tag=tag).exists()

    response = client.post(path=url, data={})

    assert response.status_code == 302
    assert TagSubscription.objects.filter(user=user, tag=tag).exists()


def test_unsubscribe(user):
    tag = TagFactory()
    client = Client()
    client.force_login(user)
    url = reverse("interactions:unsubscribe-from-tag", args=[tag.pk])

    tag_subscriptions.subscribe(tag=tag, user=user)
    assert TagSubscription.objects.filter(user=user, tag=tag).exists()

    response = client.post(path=url, data={})

    assert response.status_code == 302
    assert not TagSubscription.objects.filter(user=user, tag=tag).exists()
