from peoplefinder.models import UkStaffLocation


def get_uk_city_locations() -> list[tuple[str]]:
    cities = (
        UkStaffLocation.objects.order_by("city")
        .values_list("city", flat=True)
        .distinct()
    )
    return [(city, city) for city in cities]
