from django.http import (
    HttpResponse,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from core.models.tags import Tag
from interactions.services import tag_subscriptions as tag_subscriptions_service


@require_http_methods(["POST"])
def subscribe(request, *, tag_pk: int) -> HttpResponse:
    user = request.user
    tag = Tag.objects.get(pk=tag_pk)
    tag_subscriptions_service.subscribe(tag=tag, user=user)
    return redirect(reverse("tag_index", kwargs={"slug": tag.slug}))


@require_http_methods(["POST"])
def unsubscribe(request, *, tag_pk: int) -> HttpResponse:
    user = request.user
    tag = Tag.objects.get(pk=tag_pk)
    tag_subscriptions_service.unsubscribe(tag=tag, user=user)
    return redirect(reverse("tag_index", kwargs={"slug": tag.slug}))
