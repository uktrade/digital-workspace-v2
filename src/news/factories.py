import factory
import wagtail_factories
from django.contrib.auth import get_user_model

from news import models
from working_at_dit.tests.factories import PageWithTopicsFactory


class NewsPageFactory(PageWithTopicsFactory, wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"News page {n+1}")

    class Meta:
        model = models.NewsPage


class CommentFactory(factory.django.DjangoModelFactory):
    author = factory.Sequence(
        lambda n: get_user_model().objects.create(username=f"user_{n+1}")
    )

    content = "a comment"
    page = factory.Sequence(
        lambda n: NewsPageFactory.create(
            title=f"News Page {n+1}",
        )
    )

    class Meta:
        model = models.Comment
