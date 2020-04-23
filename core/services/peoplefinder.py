from dataclasses import dataclass
from json.decoder import JSONDecodeError
from logging import getLogger

import requests
from django.conf import settings

LOGGER = getLogger(__name__)

TIMEOUT = 2  # seconds


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


class PeoplefinderException(Exception):
    """Raised when People Finder responds with something unexpected"""


def get_user_profile(user_id):
    LOGGER.debug("Requesting profile for %s", user_id)

    try:
        profile = request("/people", {"ditsso_user_id": user_id})
    except PeoplefinderException:
        LOGGER.warning("Could not get profile for %s", user_id)
        return None

    if profile and profile["data"]:
        return PeoplefinderProfile(
            name=profile["data"]["attributes"]["name"],
            first_name=profile["data"]["attributes"]["given-name"],
            last_name=profile["data"]["attributes"]["surname"],
            profile_image_url=profile["data"]["links"].get("profile-image-url"),
            view_profile_url=profile["data"]["links"]["profile"],
            edit_profile_url=profile["data"]["links"]["edit-profile"],
            completion_percentage=profile["data"]["attributes"]["completion-score"]
        )
    else:
        LOGGER.info("No profile found for %s", user_id)
        return MissingPeoplefinderProfile(
            setup_profile_url=settings.PEOPLEFINDER_URL
        )


def request(path, params=None):
    url = settings.PEOPLEFINDER_API_URL
    full_url = url + path

    headers = {"Authorization": f"Token token={settings.PEOPLEFINDER_API_KEY}"}

    LOGGER.debug(
        "Requesting from People Finder at '%s' with params %s",
        full_url,
        params
    )

    try:
        response = requests.get(
            full_url,
            params=params, headers=headers, timeout=TIMEOUT
        )

        if response.ok:
            return response.json()
        else:
            LOGGER.warning(
                "Non-200 response (%s) from People Finder: %s",
                response.status_code,
                response.text
            )
            return None
    except (requests.exceptions.RequestException, JSONDecodeError):
        LOGGER.error("Failed to get or parse People Finder response", exc_info=True)

        raise PeoplefinderException("Could not get or parse response")
