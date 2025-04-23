from django.conf import settings
from django.db.models import QuerySet

from peoplefinder.models import Person
from user.models import User


def get_people(user: User) -> QuerySet[Person]:
    """
    Returns all the people that the given user has permission to see
    """
    queryset = Person.objects.all().get_annotated().order_by("first_name")

    if not user.has_perm("peoplefinder.can_view_inactive_profiles"):
        days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
        queryset = queryset.active_or_inactive_within(days=days)

    return queryset
