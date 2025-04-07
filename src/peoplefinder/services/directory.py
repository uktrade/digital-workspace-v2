from django.conf import settings
from django.db.models import QuerySet

from peoplefinder.models import Person
from user.models import User


def get_people(user: User) -> QuerySet[Person]:
    if user.has_perm("peoplefinder.can_view_inactive_profiles"):
        return Person.objects.all()
    days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
    return Person.objects.active_or_inactive_within(days=days)
