from django.conf import settings
from django.db.models import QuerySet

from peoplefinder.filters import DiscoverFilters
from peoplefinder.models import Person
from user.models import User


def get_people(user: User) -> QuerySet[Person]:
    """
    Returns all the people that the given user has permission to see
    """
    queryset = Person.objects.active_or_inactive_within(days=90)

    if user.has_perm(
            "peoplefinder.can_view_inactive_profiles"
        ):
        queryset = Person.objects.all()

    queryset = (
        queryset
        .order_by(
            "grade",
            "first_name",
            "last_name",
        )
        .select_related(
            "uk_office_location",
        )
        .prefetch_related(
            "roles",
            "roles__team",
        )
    )

    if not user.has_perm("peoplefinder.can_view_inactive_profiles"):
        days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
        queryset = queryset.active_or_inactive_within(days=days)

    return queryset


def get_people_with_filters(
    *,
    filter_options: dict,
    user: User,
) -> DiscoverFilters:

    return DiscoverFilters(data=filter_options, queryset=get_people(user=user))
