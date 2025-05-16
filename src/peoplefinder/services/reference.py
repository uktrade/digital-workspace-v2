from core.utils import add_null_option, cache_for, get_data_for_django_filters_choices
from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Profession,
    Team,
    UkStaffLocation,
)


@cache_for(hours=1)
def get_uk_city_locations() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=UkStaffLocation, field_name="city")


@cache_for(hours=1)
def get_uk_buildings() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(
        model=UkStaffLocation, field_name="building_name"
    )


@cache_for(hours=1)
def get_grades() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=Grade, field_name="name")


@cache_for(hours=1)
def get_professions() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=Profession, field_name="name")


@cache_for(hours=1)
def get_key_skills() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=KeySkill, field_name="name")


@cache_for(hours=1)
def get_learning_interests() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(
        model=LearningInterest, field_name="name"
    )


@cache_for(hours=1)
def get_networks() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=Network, field_name="name")


@cache_for(hours=1)
def get_additional_roles() -> list[tuple[str, str]]:
    return get_data_for_django_filters_choices(model=AdditionalRole, field_name="name")


@cache_for(hours=1)
def get_teams() -> list[tuple[str, str]]:
    qs = Team.objects.prefetch_related("parents").order_by("parents__depth")
    ids = []
    data = []
    for team in qs[0].parents.all():
        if team.pk not in ids:
            ids.append(team.pk)
            data.append(
                (
                    team.child.pk,
                    team.child.name.rjust(
                        len(team.child.name) + team.depth,
                        " ",  # Medium Mathematical Space (MMSP) U+205F
                    ),
                )
            )
    return add_null_option(choices=data)
