from django.conf import settings
from django.db.models import QuerySet

from peoplefinder.filters import DiscoverFilters
from peoplefinder.models import Person
from user.models import User


def get_people(user: User) -> QuerySet[Person]:
    """
    Returns all the people that the given user has permission to see
    """
    queryset = (
        Person.objects.all()
        .get_annotated()
        .order_by(
            "grade",
            "first_name",
            "last_name",
        )
    )

    if not user.has_perm("peoplefinder.can_view_inactive_profiles"):
        days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
        queryset = queryset.active_or_inactive_within(days=days)

    return queryset


def get_people_with_filters(
    *,
    filter_options: dict,
    queryset: QuerySet[Person],
) -> QuerySet[Person]:
    return DiscoverFilters(data=filter_options, queryset=queryset)
