import factory

from content.models import ContentPage


class ContentPageFactory(factory.Factory):
    class Meta:
        model = ContentPage
