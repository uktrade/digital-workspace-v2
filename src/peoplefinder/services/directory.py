from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet

from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Person,
    Profession,
    UkStaffLocation,
)
from user.models import User


def get_people(user: User) -> QuerySet[Person]:
    """
    Returns all the people that the given user has permission to see
    """
    queryset = Person.objects.all().get_annotated()

    if not user.has_perm("peoplefinder.can_view_inactive_profiles"):
        days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
        queryset = queryset.active_or_inactive_within(days=days)

    return queryset


def get_uk_city_locations() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.directory.get_uk_city_locations"

    if not (formatted_cities := cache.get(key=cache_key)):
        cities = (
            UkStaffLocation.objects.order_by("city")
            .values_list("city", flat=True)
            .distinct()
        )
        formatted_cities = [(city, city) for city in cities]
        cache.set(key=cache_key, value=formatted_cities, timeout=60 * 60)

    return formatted_cities


def get_uk_buildings() -> list[tuple[str]]:
    buildings = (
        UkStaffLocation.objects.order_by("building_name")
        .values_list("building_name", flat=True)
        .distinct()
    )
    return [(building, building) for building in buildings]


def get_grades() -> list[tuple[str]]:
    grades = Grade.objects.order_by("name").values_list("name", flat=True).distinct()
    return [(grade, grade) for grade in grades]


def get_professions() -> list[tuple[str]]:
    professions = (
        Profession.objects.order_by("name").values_list("name", flat=True).distinct()
    )
    return [(profession, profession) for profession in professions]


def get_key_skills() -> list[tuple[str]]:
    key_skills = (
        KeySkill.objects.order_by("name").values_list("name", flat=True).distinct()
    )
    return [(skill, skill) for skill in key_skills]


def get_learning_interests() -> list[tuple[str]]:
    learning_interests = (
        LearningInterest.objects.order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )
    return [
        (learning_interest, learning_interest)
        for learning_interest in learning_interests
    ]


def get_networks() -> list[tuple[str]]:
    networks = (
        Network.objects.order_by("name").values_list("name", flat=True).distinct()
    )
    return [(network, network) for network in networks]


def get_additional_roles() -> list[tuple[str]]:
    additional_roles = (
        AdditionalRole.objects.order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )
    return [(role, role) for role in additional_roles]
