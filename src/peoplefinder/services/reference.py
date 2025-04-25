from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Profession,
    UkStaffLocation,
)
from peoplefinder.utils import cache_for_one_hour, get_filter_data


@cache_for_one_hour
def get_uk_city_locations() -> list[tuple[str]]:
    return get_filter_data(model=UkStaffLocation, field_name="city")


@cache_for_one_hour
def get_uk_buildings() -> list[tuple[str]]:
    return get_filter_data(model=UkStaffLocation, field_name="building_name")


@cache_for_one_hour
def get_grades() -> list[tuple[str]]:
    return get_filter_data(model=Grade, field_name="name")


@cache_for_one_hour
def get_professions() -> list[tuple[str]]:
    return get_filter_data(model=Profession, field_name="name")


@cache_for_one_hour
def get_key_skills() -> list[tuple[str]]:
    return get_filter_data(model=KeySkill, field_name="name")


@cache_for_one_hour
def get_learning_interests() -> list[tuple[str]]:
    return get_filter_data(model=LearningInterest, field_name="name")


@cache_for_one_hour
def get_networks() -> list[tuple[str]]:
    return get_filter_data(model=Network, field_name="name")


@cache_for_one_hour
def get_additional_roles() -> list[tuple[str]]:
    return get_filter_data(model=AdditionalRole, field_name="name")
