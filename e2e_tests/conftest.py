"""
A conftest module to support the running of multiple e2e tests.

This module overrides how pytest-django sets up the database for each test in
this package.

First a template database is created from the test database. Then after each
test within `db_needs_reset`, the test database is dropped and replaced with a
copy of the template database. This gets around the `TransactionTestCase`
limitation of truncating the database after each test.

At the time of writing, the whole process of dropping and copying a database
for each test adds around 500ms to each test. As we expect the number of e2e
tests requiring this to be small, this overhead is fine.
"""

import os
from typing import Any

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from pytest_django.fixtures import (
    skip_if_no_django,
)
from .db_utils import (
    TEMPLATE_DATABASE_PREFIX,
    create_template_db,
    drop_dbs,
    recreate_db,
)
from .utils import login


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(scope="session")
def django_db_modify_db_settings(
    django_db_modify_db_settings_parallel_suffix: None,
) -> None:
    """
    Overrides pytest-django fixture with same sig and scope to create test
    settings and DB based on postgres config of main DB.

    Used as a fixture by django_db_setup.
    """
    skip_if_no_django()

    db_settings = settings.DATABASES["default"]
    test_name = db_settings.get("TEST", {}).get("NAME")
    if not test_name:
        test_name = f"test_{db_settings['NAME']}"  # django default name
    db_settings.setdefault("TEST", {})
    db_settings["NAME"] = test_name
    db_settings["MIGRATE"] = False
    db_settings["TEMPLATE"] = f"{TEMPLATE_DATABASE_PREFIX}{test_name}"

    # directly create new clean DB
    recreate_db(use_template=False)


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker, django_db_modify_db_settings) -> None:
    """
    Overrides pytest-django fixture with same sig and scope to populate all
    fixture data and create template DB for quicker DB resets if needed between
    functions.
    """
    # run django commands for full DB fixture setup
    with django_db_blocker.unblock():
        call_command("migrate")
        call_command("loaddata", "countries.json")
        call_command("create_menus")
        call_command("create_section_homepages")
        call_command("create_groups")
        call_command("create_people_finder_groups")
        # call_command("update_index")

    for connection in connections.all():
        connection.close()

    # create template of new DB
    create_template_db()

    yield  # run all tests

    # cleanup at end of session
    drop_dbs()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def superuser(django_db_blocker, django_user_model, browser):
    email = "test.user@example.com"

    user, _ = django_user_model.objects.get_or_create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email=email,
        legacy_sso_user_id="legacy-test-user-id",
        is_staff=True,
        is_superuser=True,
    )
    user.set_password("password")
    user.save()

    with django_db_blocker.unblock():
        call_command("create_test_teams")
        call_command("create_user_profiles")

    login(browser, user)

    return user


@pytest.fixture
def user(django_db_blocker, django_user_model):
    user, _ = django_user_model.objects.get_or_create(
        username="john.smith-1234abcd@digital.trade.gov.uk",
        first_name="John",
        last_name="Smith",
        email="john.smith@digital.trade.gov.uk",
        legacy_sso_user_id="1234abcd-1234-abcd-1234-abcd1234abcd",
    )
    user.set_password("password")
    user.save()

    with django_db_blocker.unblock():
        call_command("create_user_profiles")
