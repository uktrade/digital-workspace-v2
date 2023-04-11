import factory
import wagtail_factories

from news import models


class NewsPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"News page {n+1}")

    class Meta:
        model = models.NewsPage
