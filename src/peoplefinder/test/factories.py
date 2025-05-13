import factory

from peoplefinder.models import (
    Person,
    Team,
)
from user.test.factories import UserFactory


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person


class UserWithPersonFactory(UserFactory):
    @factory.post_generation
    def create_profile(self, create, extracted, **kwargs):
        if not getattr(self, "profile", None):
            PersonFactory(user=self)


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory class which defaults to DBT."""

    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n + 1}")
    abbreviation = factory.Sequence(lambda n: f"T{n + 1}")
    slug = factory.Sequence(lambda n: f"team-{n + 1}")
