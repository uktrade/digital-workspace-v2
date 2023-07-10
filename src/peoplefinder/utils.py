from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from peoplefinder.models import Person

PROFILE_COMPLETION_FIELDS: Dict[str, int] = {
    "first_name": 0,
    "last_name": 0,
    "photo": 1,
    "email": 0,
    "primary_phone_number": 1,
    "country": 1,
    "town_city_or_region": 1,
    "manager": 1,
    "roles": 1,  # Related objects
}


def get_profile_completion(person: "Person") -> int:
    complete_fields = 0
    field_statuses = profile_completion_field_statuses(person)
    for field_status in field_statuses:
        if field_statuses[field_status]:
            complete_fields += PROFILE_COMPLETION_FIELDS[field_status]

    total_field_weights = sum(PROFILE_COMPLETION_FIELDS.values())
    percentage = (complete_fields / total_field_weights) * 100
    return int(percentage)


def profile_completion_field_statuses(person: "Person") -> Dict[str, bool]:
    statuses: Dict[str, bool] = {}
    for profile_completion_field in PROFILE_COMPLETION_FIELDS:
        profile_completion_field_status = False
        if profile_completion_field == "roles":
            # If the person doesn't have a PK then there can't be any relationships.
            if person.pk and person.roles.all().exists():
                profile_completion_field_status = True
        elif getattr(person, profile_completion_field, None) is not None:
            profile_completion_field_status = True
        statuses[profile_completion_field] = profile_completion_field_status
    return statuses
