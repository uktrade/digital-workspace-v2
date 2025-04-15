from peoplefinder.models import UkStaffLocation


def get_uk_locations() -> list[tuple[str]]:
    cities = UkStaffLocation.objects.values_list("city", flat=True).distinct()
    return [(city, city) for city in cities]


def get_uk_buildings() -> list[tuple[str]]:
    buildings = UkStaffLocation.objects.values_list(
        "building_name", flat=True
    ).distinct()
    return [(building, building) for building in buildings]
