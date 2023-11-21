import factory

from peoplefinder.models import Person, Team


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory class which defaults to DIT."""

    class Meta:
        model = Team

    name = "Department for International Trade"
    abbreviation = "DIT"
    slug = "department-for-international-trade"
