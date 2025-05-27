import zoneinfo

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve
from django.utils import timezone

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
                profile = Person.objects.get(user=request.user)
            except Person.DoesNotExist:
                profile = None

            response.context_data["peoplefinder_profile"] = profile

        return response


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except Person.DoesNotExist:
                timezone.activate(settings.LOCAL_TIME_ZONE)
            else:
                timezone.activate(zoneinfo.ZoneInfo(profile.timezone))
        else:
            timezone.activate(settings.LOCAL_TIME_ZONE)
        return self.get_response(request)
