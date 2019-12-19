from dataclasses import dataclass
from logging import getLogger
import os

import requests

LOGGER = getLogger(__name__)

@dataclass
class PeoplefinderProfile:
    """A user profile from People Finder"""

    name: str
    first_name: str
    last_name: str
    profile_image_url: str
    view_profile_url: str
    edit_profile_url: str
    completion_percentage: int

    @staticmethod
    def is_blank():
        return False

    def is_complete(self):
        return self.completion_percentage == 100


@dataclass
class MissingPeoplefinderProfile:
    """Represents a missing profile (e.g. when the user does not have one set up)"""

    setup_profile_url: str

    @staticmethod
    def is_blank():
        return True


class GetPeoplefinderProfileMiddleware:
    """Inject current user details from People Finder into view context

    We need access to certain user details on every page (e.g. name,
    profile picture, profile edit URL) for the profile header.
    """

    def __init__(self, get_response):
        self.__people_finder_api_key = os.environ["PEOPLEFINDER_API_KEY"]
        self.__people_finder_url = os.environ["PEOPLEFINDER_URL"]
        self.__people_finder_api_url = os.environ["PEOPLEFINDER_API_URL"]

        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if response.context_data:
            profile = self.__get_user_profile(request.user.username)
            response.context_data["peoplefinder_profile"] = profile

        return response

    def __get_user_profile(self, user_id):
        LOGGER.debug("Getting profile for %s from %s", user_id, self.__people_finder_api_url)

        url = f"{self.__people_finder_api_url}?ditsso_user_id={user_id}"
        headers = {"Authorization": f"Token token={self.__people_finder_api_key}"}

        try:
            response = requests.get(url, headers=headers)

            if response.ok:
                result = response.json()["data"]

                return PeoplefinderProfile(
                    name=result["attributes"]["name"],
                    first_name=result["attributes"]["given-name"],
                    last_name=result["attributes"]["surname"],
                    profile_image_url=result["links"].get("profile-image-url"),
                    view_profile_url=result["links"]["profile"],
                    edit_profile_url=result["links"]["edit-profile"],
                    completion_percentage=result["attributes"]["completion-score"]
                )

            if response.status_code == 404:
                return MissingPeoplefinderProfile(setup_profile_url=self.__people_finder_url)

            return None
        except (requests.exceptions.RequestException, KeyError):
            LOGGER.warning("Could not get user profile for user %s", user_id, exc_info=True)

            return None
