from importlib import import_module

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY


base_url = "http://localhost:8000"

# https://docs.djangoproject.com/en/3.2/topics/http/sessions/#using-sessions-out-of-views
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


def login(page, user):
    # Manually create the session to bypass auth.
    session = SessionStore()
    session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    cookie = {
        "name": settings.SESSION_COOKIE_NAME,
        "value": session.session_key,
        "url": f"{base_url}/",
    }

    page.goto(f"{base_url}/")  # ensures a context should exist
    context = page.context
    context.add_cookies(
        [
            cookie,
        ]
    )
