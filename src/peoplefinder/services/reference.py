from typing import Any

from django.core.cache import cache

from peoplefinder.models import (
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Profession,
    UkStaffLocation,
)


def query_data(*, model: Any, field_name: str) -> list[tuple[str]]:
    data = (
        model.objects.order_by(field_name).values_list(field_name, flat=True).distinct()
    )
    return [(value, value) for value in data]


def get_uk_city_locations() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_uk_city_locations"

    if not (cities := cache.get(key=cache_key)):
        cities = query_data(model=UkStaffLocation, field_name="city")
        cache.set(key=cache_key, value=cities, timeout=60 * 60)

    return cities


def get_uk_buildings() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_uk_buildings"

    if not (building_names := cache.get(key=cache_key)):
        building_names = query_data(model=UkStaffLocation, field_name="building_name")
        cache.set(key=cache_key, value=building_names, timeout=60 * 60)

    return building_names


def get_grades() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_grades"

    if not (grades := cache.get(key=cache_key)):
        grades = query_data(model=Grade, field_name="name")
        cache.set(key=cache_key, value=grades, timeout=60 * 60)

    return grades


def get_professions() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_professions"

    if not (professions := cache.get(key=cache_key)):
        professions = query_data(model=Profession, field_name="name")
        cache.set(key=cache_key, value=professions, timeout=60 * 60)

    return professions


def get_key_skills() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_key_skills"

    if not (key_skills := cache.get(key=cache_key)):
        key_skills = query_data(model=KeySkill, field_name="name")
        cache.set(key=cache_key, value=key_skills, timeout=60 * 60)

    return key_skills


def get_learning_interests() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_learning_interests"

    if not (learning_interests := cache.get(key=cache_key)):
        learning_interests = query_data(model=LearningInterest, field_name="name")
        cache.set(key=cache_key, value=learning_interests, timeout=60 * 60)

    return learning_interests


def get_networks() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_networks"

    if not (networks := cache.get(key=cache_key)):
        networks = query_data(model=Network, field_name="name")
        cache.set(key=cache_key, value=networks, timeout=60 * 60)

    return networks


def get_additional_roles() -> list[tuple[str]]:
    cache_key = "peoplefinder.services.reference.get_additional_roles"

    if not (additional_roles := cache.get(key=cache_key)):
        additional_roles = query_data(model=Network, field_name="name")
        cache.set(key=cache_key, value=additional_roles, timeout=60 * 60)

    return additional_roles
