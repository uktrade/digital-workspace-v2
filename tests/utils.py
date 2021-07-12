from importlib import import_module

from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
)

# https://docs.djangoproject.com/en/3.2/topics/http/sessions/#using-sessions-out-of-views
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

# The host must match the `--name` value passed to `docker-compose run`.
# The port must match the port given in the `--liveserver` value.
URL = "http://liveserver:8000/"


def login(selenium, user):
    # Manually create the session to bypass SSO.
    session = SessionStore()
    session[SESSION_KEY] = user.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    cookie = {
        "name": settings.SESSION_COOKIE_NAME,
        "value": session.session_key,
    }

    # Navigate to the homepage so we can set the cookie.
    selenium.get(URL)
    # Set the cookie.
    selenium.add_cookie(cookie)
    # Refresh the page now that we are logged in.
    selenium.refresh()
