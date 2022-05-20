from peoplefinder.models import Person


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

        profile = None

        if request.user.is_authenticated:
            profile = Person.objects.with_profile_completion().get(user=request.user)

        response.context_data["peoplefinder_profile"] = profile

        return response
