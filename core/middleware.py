from django.conf import settings

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

        # TODO: Remove once we have migrated to peoplefinder v2 in prod.
        response.context_data["peoplefinder_v2"] = settings.PEOPLEFINDER_V2

        profile = peoplefinder.get_user_profile(request.user.legacy_sso_user_id)
        response.context_data["peoplefinder_profile"] = profile

        return response
