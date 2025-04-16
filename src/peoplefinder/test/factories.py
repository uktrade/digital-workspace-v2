import factory

from peoplefinder.models import Person, Team


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory class which defaults to DBT."""

    class Meta:
        model = Team

    name = "Department for Business and Trade"
    abbreviation = "DBT"
    slug = "department-for-business-and-trade"
