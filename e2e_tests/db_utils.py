import os
import psycopg2
from typing import Any

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings


TEMPLATE_DATABASE_PREFIX = "template_"


def _run_sql(sql: str, db_settings: dict[str, Any]) -> None:
    """Run the SQL query on PostgreSQL bypassing the Django ORM.

    Note this doesn't specify a DB to connect to, so it's most useful for
    creating/dropping DBs, etc.

    Args:
        sql: The query to be run.
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


def _get_db_name() -> str:
    return settings.DATABASES['default']['NAME']


def _get_template_name() -> str:
    test_name = _get_db_name()
    return f"{TEMPLATE_DATABASE_PREFIX}{test_name}"


def create_template_db(without_drop: bool=False) -> None:
    """
    Creates a new Postgres DB copied directly from the test DB, allowing future
    test runs requiring clean-but-complete-with-fixture DBs to be quickly
    copied across

    Args:
        without_drop: A flag to say whether or not to drop the template DB before trying to create it. Defaults to False
    """
    db_settings = settings.DATABASES["default"]
    test_name = _get_db_name()
    template_name = _get_template_name()

    if without_drop:
        _run_sql(
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
            db_settings,
        )
        _run_sql(f"DROP DATABASE IF EXISTS {template_name}", db_settings)
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )
    _run_sql(
        f"CREATE DATABASE {template_name} WITH TEMPLATE {test_name}",
        db_settings,
    )
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )


def recreate_db(use_template: bool=True, _retries:Any=None):
    """
    Drops the existing test DB and recreates it, either clean or from the
    existing template DB.

    Note it will fail is asked to use the template and that template doesn't
    exist.

    Args:
        use_template: A flag to determine whether or not to base the new DB on the template. Defaults to True
        _retries: An internal-use number to ensure we don't recurse forever
    """
    db_settings = settings.DATABASES["default"]
    test_name = _get_db_name()
    template_name = _get_template_name()

    # drop existing test DB
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )
    _run_sql(f"DROP DATABASE IF EXISTS {test_name}", db_settings)

    # create new test DB
    if use_template:
        sql = f"CREATE DATABASE {test_name} WITH TEMPLATE {template_name}"
    else:
        sql = f"CREATE DATABASE {test_name} WITH TEMPLATE template1"

    try:
        _run_sql(
            sql,
            db_settings,
        )
        _run_sql(
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' AND pid <> pg_backend_pid()",  # noqa: S608
            db_settings,
        )
    except:
        # first time with TESTS_KEEP_DB=1 this will break
        if _retries is None or _retries < 2:
            retries = _retries
            if _retries is None:
                retries = 0
            retries += 1

            keep_db = os.environ.get('TESTS_KEEP_DB', False)
            if keep_db:
                return recreate_db(use_template=False, _retries=retries)


def drop_dbs(only_test: bool=False):
    """
    Drops both test and template DBs or, optionally, only test DB to clean up at the end of a test run

    Args:
        only_test: A flag to determine whether or not to drop only the test DB, preserving the template DB. Defaults to False
    """
    db_settings = settings.DATABASES["default"]
    test_name = _get_db_name()
    template_name = _get_template_name()
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' OR pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )
    _run_sql(f"DROP DATABASE IF EXISTS {test_name}", db_settings)
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )
    if not only_test:
        _run_sql(f"DROP DATABASE IF EXISTS {template_name}", db_settings)
        _run_sql(
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' OR pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
            db_settings,
        )
