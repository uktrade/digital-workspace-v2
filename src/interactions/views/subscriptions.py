from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
from waffle import flag_is_active

from core import flags
from interactions.services import tag_subscriptions as tag_sub_service


def manage_subscriptions(request: HttpRequest) -> HttpResponse:
    if not any(
        [
            flag_is_active(request, flags.TAG_FOLLOWING),
            flag_is_active(request, flags.TEAM_FOLLOWING),
            flag_is_active(request, flags.NETWORK_FOLLOWING),
            flag_is_active(request, flags.PERSON_FOLLOWING),
        ]
    ):
        return HttpResponseForbidden()

    context: dict[str, str] = {"page_title": "Subscriptions"}
    context.update(
        subscribed_tags=tag_sub_service.get_subscribed_tags(user=request.user),
        subscribed_teams=tag_sub_service.get_subscribed_tags(user=request.user),
        subscribed_networks=tag_sub_service.get_subscribed_tags(user=request.user),
        subscribed_people=tag_sub_service.get_subscribed_tags(user=request.user),
    )
    return TemplateResponse(request, "interactions/manage_subscriptions.html", context)
