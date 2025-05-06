import pytest

from django.test import override_settings, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from waffle.testutils import override_flag

from core.utils import get_all_feature_flags


pytestmark = pytest.mark.django_db


@override_settings(CACHE_FLAGS_IN_SESSION=True)
def test_get_all_feature_flags_session_cache():
    # setup client request
    request = RequestFactory().get("/")
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    # verify session value is empty
    assert len(request.session.items()) == 0
    # setup a flag
    with override_flag("dummy_new_flag", active=True):
        # hit get_all_feature_flags to retrieve
        flags = get_all_feature_flags(request)
        # verify session value is not empty
        assert len(request.session.items()) > 0
        assert request.session["all_feature_flags"] == flags
        assert flags["dummy_new_flag"] is True

    # change a flag
    with override_flag("dummy_new_flag", active=False):
        new_flags = get_all_feature_flags(request)
        assert new_flags == flags
        # verify session value is not empty
        assert len(request.session.items()) > 0
        assert request.session["all_feature_flags"] == flags
        assert new_flags["dummy_new_flag"] is True


@override_settings(CACHE_FLAGS_IN_SESSION=False)
def test_get_all_feature_flags_session_cache_disabled():
    # setup client request
    request = RequestFactory().get("/")
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    # verify session value is empty
    assert len(request.session.items()) == 0
    # setup a flag
    with override_flag("dummy_new_flag", active=True):
        # hit get_all_feature_flags to retrieve
        flags = get_all_feature_flags(request)
        # verify session value is not empty
        assert len(request.session.items()) == 0
        assert flags["dummy_new_flag"] is True

    # change a flag
    with override_flag("dummy_new_flag", active=False):
        new_flags = get_all_feature_flags(request)
        assert new_flags != flags
        # verify session value is not empty
        assert len(request.session.items()) == 0
        assert new_flags["dummy_new_flag"] is False
