from django.db import DatabaseError

from content.models import ContentPage


class CheckDatabase:
    name = "database"

    def check(self):
        try:
            ContentPage.objects.all().exists()
            return True, ""
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase,)
