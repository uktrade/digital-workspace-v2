import factory
import factory.fuzzy

from peoplefinder.models import Person, Team, UkStaffLocation
from user.models import User
from user.test.factories import UserFactory
from django.core.management import call_command


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    legacy_sso_user_id = factory.Sequence(lambda n: f"legacy_sso_{n}")

    is_active = True
    user = factory.SubFactory(UserFactory)
    uk_office_location = factory.Iterator(UkStaffLocation.objects.all())
    first_name = factory.fuzzy.FuzzyText(length=12)
    preferred_first_name = factory.fuzzy.FuzzyText(length=12)
    last_name = factory.fuzzy.FuzzyText(length=12)


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
