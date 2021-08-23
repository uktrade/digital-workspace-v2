from django.conf import settings

from peoplefinder.models import Person
from .services import peoplefinder


class GetPeoplefinderProfileMiddleware:
    """Inject current user details from People Finder into view context

    We need access to certain user details on every page (e.g. name,
    profile picture, profile edit URL) for the profile header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if not response.context_data:
            return response

        use_peoplefinder_v2 = (
            settings.PEOPLEFINDER_V2 and request.user.is_using_peoplefinder_v2
        )

        # TODO: Remove once we have migrated to peoplefinder v2 in prod.
        response.context_data["peoplefinder_v2"] = use_peoplefinder_v2

        profile = None

        if request.user.is_authenticated:
            if use_peoplefinder_v2:
                profile = Person.objects.with_profile_completion().get(
                    pk=request.user.pk
                )
                legacy_profile = peoplefinder.get_user_profile(
                    request.user.legacy_sso_user_id
                )
                response.context_data["legacy_peoplefinder_profile"] = legacy_profile
            else:
                profile = peoplefinder.get_user_profile(request.user.legacy_sso_user_id)

        response.context_data["peoplefinder_profile"] = profile

        return response
