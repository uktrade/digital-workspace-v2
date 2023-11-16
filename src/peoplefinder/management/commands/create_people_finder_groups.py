from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


PERSON_ADMIN_GROUP_NAME = "Person Admin"
PERSON_ADMIN_PERMS = [
    "change_person",
    "delete_person",
    "view_auditlog",
    "can_view_inactive_profiles",
]

TEAM_ADMIN_GROUP_NAME = "Team Admin"
TEAM_ADMIN_PERMS = [
    "add_team",
    "change_team",
    "delete_team",
    "view_auditlog",
]


class Command(BaseCommand):
    help = "Create groups with permissions for peoplefinder"

    def handle(self, *args, **options):
        # Person Admin
        person_admin, _ = Group.objects.get_or_create(
            name=PERSON_ADMIN_GROUP_NAME,
        )
        person_admin_perms = Permission.objects.filter(
            codename__in=PERSON_ADMIN_PERMS,
            content_type__app_label="peoplefinder",
        )
        person_admin.permissions.set(person_admin_perms)
        person_admin.save()

        # Team Admin
        team_admin, _ = Group.objects.get_or_create(
            name=TEAM_ADMIN_GROUP_NAME,
        )
        team_admin_perms = Permission.objects.filter(
            codename__in=TEAM_ADMIN_PERMS,
            content_type__app_label="peoplefinder",
        )
        team_admin.permissions.set(team_admin_perms)
        team_admin.save()
