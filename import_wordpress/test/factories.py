import factory

from wagtail.images.models import Image as WagtailImage


class WagtailImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WagtailImage

    title = "test"
    width = 100
    height = 100
    file_size = 1
