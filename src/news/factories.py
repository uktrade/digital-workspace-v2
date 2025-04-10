import factory
import factory.fuzzy
import wagtail_factories

from news import models
from peoplefinder.test.factories import UserWithPersonFactory
from working_at_dit.tests.factories import PageWithTopicsFactory


class NewsPageFactory(PageWithTopicsFactory, wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"News page {n + 1}")

    class Meta:
        model = models.NewsPage


class CommentFactory(factory.django.DjangoModelFactory):
    author = factory.SubFactory(UserWithPersonFactory)
    content = factory.fuzzy.FuzzyText(length=50)
    page = factory.SubFactory(NewsPageFactory)

    class Meta:
        model = models.Comment
