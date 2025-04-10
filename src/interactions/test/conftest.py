import pytest
from about_us.models import AboutUs
from news.models import NewsPage

from peoplefinder.test.factories import UserWithPersonFactory


@pytest.fixture
def user():
    return UserWithPersonFactory()


@pytest.fixture
def news_page():
    return NewsPage.objects.create(
        title="News",
        depth=1,
        path="page2",
    )


@pytest.fixture
def about_page():
    return AboutUs.objects.create(
        title="About Us",
        depth=4,
        path="page1",
    )
