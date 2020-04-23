from json.decoder import JSONDecodeError
from logging import getLogger

import requests
from django.conf import settings

LOGGER = getLogger(__name__)

# Balance between decent response time and WP sluggishness
TIMEOUT = 2  # seconds


def wp_request(path, params=None):
    return __wp_request(
        settings.LEGACY_WORDPRESS_API_URL,
        path,
        params
    )


def wp_custom_request(path, params=None):
    return __wp_request(
        settings.LEGACY_WORDPRESS_API_CUSTOM_URL,
        path,
        params
    )


def __wp_request(url, path, params=None):
    full_url = url + path
    headers = {"Authorization": f"Basic {settings.LEGACY_WORDPRESS_API_KEY}"}

    LOGGER.debug("Requesting from Wordpress at '%s' with params %s", full_url, params)

    try:
        response = requests.get(
            full_url,
            params=params, headers=headers, timeout=TIMEOUT
        )

        if response.ok:
            return (response.headers, response.json())
        else:
            LOGGER.error(
                "Non-OK (%s) response from Wordpress: '%s'",
                response.status_code,
                response.text
            )

            return None
    except (requests.exceptions.RequestException, JSONDecodeError):
        LOGGER.error("Failed to get or parse Wordpress response", exc_info=True)

        return None
