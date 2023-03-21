from importlib import import_module

from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
)


# https://docs.djangoproject.com/en/3.2/topics/http/sessions/#using-sessions-out-of-views
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


def login(browser, user):
    # Manually create the session to bypass auth.
    session = SessionStore()
    session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    cookie = {
        "name": settings.SESSION_COOKIE_NAME,
        "value": session.session_key,
        "url": "http://wagtail:8000/",
        "sameSite": "None",
    }

    print("vvvvvvvvvvv")
    if (len(browser.contexts) == 0):
        browser.new_context()
    for context in browser.contexts:
        context.add_cookies([cookie, ])
        print(context.cookies())
    page = browser.new_page()
    page.goto("/")

    for context in browser.contexts:
        print(context.cookies())
    print(user)
    print(cookie)
    print(session)
    print("^^^^^^^^^^")
