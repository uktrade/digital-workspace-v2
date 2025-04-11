import factory

from peoplefinder.models import Person, Team
from user.models import User
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

    name = "Department for Business and Trade"
    abbreviation = "DBT"
    slug = "department-for-business-and-trade"
