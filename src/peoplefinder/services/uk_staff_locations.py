from typing import TypedDict

from django.db import connections

from peoplefinder.models import UkStaffLocation


class IngestOutput(TypedDict):
    created: int
    updated: int
    deleted: int


class UkStaffLocationService:
    def ingest_uk_staff_locations(self) -> IngestOutput:
        created = 0
        updated = 0
        deleted = 0

        # If the uk_staff_locations database is not configured, don't do
        # anything.
        if "uk_staff_locations" not in connections:
            return {
                "created": created,
                "updated": updated,
                "deleted": deleted,
            }

        existing_uk_staff_locations = list(
            UkStaffLocation.objects.all().values_list("pk", flat=True)
        )

        with connections["uk_staff_locations"].cursor() as cursor:
            cursor.execute(
                """
                SELECT location_code, location_name, city, organisation, building_name
                FROM dit.uk_staff_locations
                """
            )
            for row in cursor.fetchall():
                location_code = row[0]
                location_name = row[1]
                city = row[2]
                organisation = row[3]
                building_name = row[4]
                (
                    uk_staff_location,
                    location_created,
                ) = UkStaffLocation.objects.update_or_create(
                    code=location_code,
                    defaults={
                        "is_active": True,
                        "name": location_name,
                        "city": city,
                        "organisation": organisation,
                        "building_name": building_name,
                    },
                )

                if location_created:
                    created += 1
                else:
                    updated += 1

                if uk_staff_location.pk in existing_uk_staff_locations:
                    existing_uk_staff_locations.remove(uk_staff_location.pk)

        if existing_uk_staff_locations:
            deleted = UkStaffLocation.objects.filter(
                pk__in=existing_uk_staff_locations
            ).update(is_active=False)

        return {
            "created": created,
            "updated": updated,
            "deleted": deleted,
        }

    def get_uk_staff_location_cities(self) -> list[str]:
        return [
            c["city"]
            for c in UkStaffLocation.objects.values("city").distinct().order_by("city")
        ]
