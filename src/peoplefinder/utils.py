from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from peoplefinder.models import Person

PROFILE_COMPLETION_FIELDS = [
    "first_name",
    "last_name",
    "photo",
    "email",
    "primary_phone_number",
    "country",
    "town_city_or_region",
    "manager",
    "roles",  # Related objects
]


def get_profile_completion(person: "Person") -> int:
    complete_fields = 0
    field_statuses = profile_completion_field_statuses(person)
    for field_status in field_statuses:
        if field_statuses[field_status]:
            complete_fields += 1
    percentage = (complete_fields / len(field_statuses)) * 100
    return int(percentage)


def profile_completion_field_statuses(person: "Person") -> Dict[str, bool]:
    statuses = {}
    for profile_completion_field in PROFILE_COMPLETION_FIELDS:
        if profile_completion_field == "roles":
            if person.roles.all().exists():
                statuses[profile_completion_field] = True
            else:
                statuses[profile_completion_field] = False
            continue
        if getattr(person, profile_completion_field, None):
            statuses[profile_completion_field] = True
        else:
            statuses[profile_completion_field] = False
    return statuses
