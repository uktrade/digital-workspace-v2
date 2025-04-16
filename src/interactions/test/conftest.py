import pytest
from about_us.models import AboutUs
from news.models import NewsHome

from peoplefinder.test.factories import UserWithPersonFactory
from news.factories import NewsPageFactory


@pytest.fixture
def user():
    return UserWithPersonFactory()


@pytest.fixture
def news_page():
    news_home_page = NewsHome.objects.get()
    return NewsPageFactory(parent=news_home_page)


@pytest.fixture
def about_page():
    return AboutUs.objects.create(
        title="About Us",
        depth=4,
        path="page1",
    )
