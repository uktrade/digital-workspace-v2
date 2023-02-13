from django.shortcuts import redirect
from django.urls import resolve

from peoplefinder.models import Person


class GetPeoplefinderProfileMiddleware:
    """Inject current user details from People Finder into view context

    We need access to certain user details on every page (e.g. name,
    profile picture, profile edit URL) for the profile header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            hasattr(request.user, "profile")
            and not request.user.profile.is_active
            and resolve(request.path).url_name != "deactivated"
        ):
            return redirect("deactivated")

        response = self.get_response(request)

        return response

    def process_template_response(self, request, response):
        if not response.context_data:
            return response

        if request.user.is_authenticated:
            try:
                profile = Person.objects.with_profile_completion().get(
                    user=request.user
                )
            except Person.DoesNotExist:
                profile = None

            response.context_data["peoplefinder_profile"] = profile

        return response
