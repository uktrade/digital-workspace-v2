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
        if response.context_data:
            profile = peoplefinder.get_user_profile(request.user.username)
            response.context_data["peoplefinder_profile"] = profile

        return response
