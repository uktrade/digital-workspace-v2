import factory

from core.models.tags import Tag


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    slug = factory.Sequence(lambda n: f"tag-slug-{n + 1}")
    name = factory.Sequence(lambda n: f"Tag {n + 1}")
