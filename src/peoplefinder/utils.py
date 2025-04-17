from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Profession,
    UkStaffLocation,
)


def get_uk_city_locations() -> list[tuple[str]]:
    cities = (
        UkStaffLocation.objects.order_by("city")
        .values_list("city", flat=True)
        .distinct()
    )
    return [(city, city) for city in cities]


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
