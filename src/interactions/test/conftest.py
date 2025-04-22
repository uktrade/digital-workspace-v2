import pytest

# import os
from about_us.models import AboutUs
from news.models import NewsHome

# from django.core.management import call_command
# from django.db import connections
# from e2e_tests.db_utils import (
#     create_template_db,
#     drop_dbs,
# )

# os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from peoplefinder.test.factories import UserWithPersonFactory
from news.factories import NewsPageFactory


@pytest.fixture
def user():
    return UserWithPersonFactory()


@pytest.fixture
def news_page():
    news_home_page = NewsHome.objects.first()
    return NewsPageFactory(parent=news_home_page)


@pytest.fixture
def about_page():
    return AboutUs.objects.create(
        title="About Us",
        depth=4,
        path="page1",
    )


# @pytest.fixture(scope="session")
# def django_db_setup(
#     django_db_blocker,
#     django_db_keepdb,
#     django_db_modify_db_settings,
#     live_server,
# ) -> None:
#     """
#     Overrides pytest-django fixture with same sig and scope to populate all
#     fixture data and create template DB for quicker DB resets if needed between
#     functions.
#     """
#     keep_db = os.environ.get("TESTS_KEEP_DB", False)

# run django commands for full DB fixture setup
# with django_db_blocker.unblock():
# call_command("migrate")
# call_command("loaddata", "countries.json")
# call_command("create_section_homepages")
# call_command("create_menus")
# call_command("create_groups")
# call_command("create_people_finder_groups")
# call_command("update_index")

# for connection in connections.all():
#     connection.close()

# if keep_db:
#     create_template_db(drop_first=False)
# else:
#     # create template of new DB
#     create_template_db()

# yield  # run all tests

# # cleanup at end of session
# if keep_db:
#     drop_dbs(only_test=True)  # preserve template DB
# else:
#     drop_dbs()
