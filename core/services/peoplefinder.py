import datetime
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from logging import getLogger

import jwt
import requests
from django.conf import settings

LOGGER = getLogger(__name__)


@dataclass
class PeoplefinderProfile:
    """A user profile from People Finder"""

    email: str
    name: str
    first_name: str
    completion_percentage: int
    profile_url: str
    profile_image_url: str

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
    if not settings.PEOPLEFINDER_PROFILE_API_PRIVATE_KEY:
        LOGGER.error(
            "Missing People Finder API private key in settings.PEOPLEFINDER_PROFILE_API_PRIVATE_KEY"
        )
        return None

    LOGGER.debug(
        "Fetching user profile for %s from %s",
        user_id,
        settings.PEOPLEFINDER_PROFILE_API_URL,
    )

    path = f"/api/v2/people_profiles/{user_id}"
    url = settings.PEOPLEFINDER_PROFILE_API_URL + path

    token = jwt.encode(
        {
            "fullpath": path,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=60),
        },
        settings.PEOPLEFINDER_PROFILE_API_PRIVATE_KEY,
        algorithm="RS512",
    )
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.ok:
            result = response.json()

            return PeoplefinderProfile(
                email=result["email"],
                name=result["name"],
                first_name=result["first_name"],
                completion_percentage=result["completion_score"],
                profile_url=result["profile_url"],
                profile_image_url=result.get("profile_image_url"),
            )

        if response.status_code == 404:
            return MissingPeoplefinderProfile(
                setup_profile_url=settings.PEOPLEFINDER_URL
            )

        LOGGER.error(
            "Unexpected response status from People Finder API (Status %s): %s",
            response.status_code,
            response.text,
        )
        return None
    except (requests.exceptions.RequestException, JSONDecodeError, KeyError):
        LOGGER.error("Could not get user profile for user %s", user_id, exc_info=True)

        return None
