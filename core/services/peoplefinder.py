from dataclasses import dataclass
from json.decoder import JSONDecodeError
from logging import getLogger

import requests
from django.conf import settings

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


def get_user_profile(user_id):
    LOGGER.debug("Getting profile for %s from %s", user_id, settings.PEOPLEFINDER_API_URL)

    url = f"{settings.PEOPLEFINDER_API_URL}?ditsso_user_id={user_id}"
    headers = {"Authorization": f"Token token={settings.PEOPLEFINDER_API_KEY}"}

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
            return MissingPeoplefinderProfile(setup_profile_url=settings.PEOPLEFINDER_URL)

        return None
    except (requests.exceptions.RequestException, JSONDecodeError, KeyError):
        LOGGER.warning("Could not get user profile for user %s", user_id, exc_info=True)

        return None
