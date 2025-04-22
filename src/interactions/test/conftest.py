import pytest


from about_us.models import AboutUs
from news.models import NewsHome


from peoplefinder.test.factories import UserWithPersonFactory
from news.factories import NewsPageFactory
from django.core.management import call_command


@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("create_section_homepages")
        call_command("loaddata", "countries.json")


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
