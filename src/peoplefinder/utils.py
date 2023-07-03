from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from peoplefinder.models import Person

PROFILE_COMPLETION_FIELDS = [
    "country",
    "town_city_or_region",
    "primary_phone_number",
    "manager",
    "photo",
    "email",
    "first_name",
    "last_name",
    "roles",  # Related objects
]


def get_profile_completion(person: "Person") -> int:
    complete_fields = 0
    for profile_completion_field in PROFILE_COMPLETION_FIELDS:
        if profile_completion_field == "roles":
            if person.roles.all().exists():
                complete_fields += 1
            continue
        if getattr(person, profile_completion_field, None):
            complete_fields += 1

    percentage = (complete_fields / len(PROFILE_COMPLETION_FIELDS)) * 100
    return int(percentage)
