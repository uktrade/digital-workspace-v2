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


def create_template_db() -> None:
    """
    Creates a new Postgres DB copied directly from the test DB, allowing future
    test runs requiring clean-but-complete-with-fixture DBs to be quickly
    copied across
    """
    db_settings = settings.DATABASES["default"]
    test_name = _get_db_name()
    template_name = _get_template_name()

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


def recreate_db(use_template: bool=True):
    """
    Drops the existing test DB and recreates it, either clean or from the
    existing template DB.

    Note it will fail is asked to use the template and that template doesn't
    exist.

    Args:
        use_template: A flag to say whether or not to base the new DB on the template. Defaults to True
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

    _run_sql(
        sql,
        db_settings,
    )
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )


def drop_dbs():
    """
    Drops both test and template DBs to clean up at the end of a test run
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
    _run_sql(f"DROP DATABASE IF EXISTS {template_name}", db_settings)
    _run_sql(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_name}' OR pg_stat_activity.datname = '{template_name}' AND pid <> pg_backend_pid()",  # noqa: S608
        db_settings,
    )
