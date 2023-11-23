import pytest
from django.core.management import call_command

from peoplefinder.models import Person, Team
from user.models import User
from content.models import BasePage


@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "countries.json")
        call_command("create_section_homepages")

        yield

        Team.objects.all().delete()
        Person.objects.all().delete()
        User.objects.all().delete()
        BasePage.objects.all().delete()
