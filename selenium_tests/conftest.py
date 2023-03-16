"""A conftest module to support the running of multiple selenium tests.

This module overrides how pytest-django sets up the database for each test in this
package.

First a template database is created from the test database. Then after each test, the
test database is dropped and replaced with a copy of the template database. This gets
around the `TransactionTestCase` limitation of truncating the database after each test.

At the time of writing, the whole process of dropping and copying a database for each
test adds around 500ms to each test. As I expect the number of selenium tests to be
small, this overhead is fine.
"""

from typing import Any

import psycopg2
import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


TEMPLATE_DATABASE_PREFIX = "template_"


def run_sql(sql: str, db_settings: dict[str, Any]) -> None:
    """Run the SQL query on PostgreSQL bypassing the Django ORM.

    Args:
        sql: The query to be ran.
        db_settings: A dict of database connection settings.
    """
    conn = psycopg2.connect(
        host=db_settings["HOST"],
        port=db_settings["PORT"],
        user=db_settings["USER"],
        password=db_settings["PASSWORD"],
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.fixture(scope="package")
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        # digital-workspace setup
        call_command("create_menus")
        call_command("create_section_homepages")
        call_command("create_groups")
        # peoplefinder setup
        call_command("loaddata", "countries.json")
        call_command("create_people_finder_groups")
        # common setup
        call_command("update_index")

    db_settings = settings.DATABASES["default"]

    test_db_name = db_settings["NAME"]
    template_db_name = TEMPLATE_DATABASE_PREFIX + test_db_name

    for connection in connections.all():
        connection.close()

    run_sql(f"DROP DATABASE IF EXISTS {template_db_name}", db_settings)
    run_sql(
        f"CREATE DATABASE {template_db_name} WITH TEMPLATE {test_db_name}",
        db_settings,
    )

    yield

    for connection in connections.all():
        connection.close()

    run_sql(f"DROP DATABASE IF EXISTS {test_db_name}", db_settings)
    run_sql(
        f"CREATE DATABASE {test_db_name} WITH TEMPLATE {template_db_name}",
        db_settings,
    )
    run_sql(f"DROP DATABASE IF EXISTS {template_db_name}", db_settings)


@pytest.fixture(scope="function", autouse=True)
def copy_database():
    db_settings = settings.DATABASES["default"]

    test_db_name = db_settings["NAME"]
    template_db_name = TEMPLATE_DATABASE_PREFIX + test_db_name

    for connection in connections.all():
        connection.close()

    run_sql(f"DROP DATABASE IF EXISTS {test_db_name}", db_settings)
    run_sql(
        f"CREATE DATABASE {test_db_name} WITH TEMPLATE {template_db_name}",
        db_settings,
    )
