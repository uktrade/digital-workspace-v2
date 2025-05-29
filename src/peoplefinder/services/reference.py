from core.utils import add_null_option, cache_for, get_data_for_django_filters_choices
from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Profession,
    TeamTree,
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
    """
    Starting with TeamTree for hierarchical ordering, we then recurse down to ensure children are under their parent item
    """

    def get_children_of(team, qs):
        return [r.child for r in qs.filter(parent__pk=team.pk)]

    def add_to_dict(qs, data_dict, team):
        data_dict[team.pk] = (team.pk, team.name)
        for child in get_children_of(team, qs):
            add_to_dict(qs, data_dict, child)

    qs = (
        TeamTree.objects.prefetch_related("parent", "child")
        .order_by("parent", "child")
        .filter(depth=1)
    )
    data: dict = {}
    for relation in qs:
        if relation.parent.pk not in data.keys():
            add_to_dict(qs, data, relation.parent)

    return add_null_option(choices=list(data.values()))
