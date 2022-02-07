from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


PERSON_EDITOR_PERMISSION_TYPES = [
    "edit_profile",
    "delete_profile",
    "edit_sso_id",
]

TEAM_EDITOR_PERMISSION_TYPES = [
    "add_subteam",
    "edit_team_profile",
    "delete_team_profile",
]


class Command(BaseCommand):
    help = "Create page permissions"

    def handle(self, *args, **options):
        person_editors, _ = Group.objects.get_or_create(
            name="Person Editors",
        )

        person_editor_permissions = Permission.objects.filter(
            codename__in=PERSON_EDITOR_PERMISSION_TYPES
        )
        person_editors.permissions.add(*person_editor_permissions)
        person_editors.save()

        team_editors, _ = Group.objects.get_or_create(
            name="Team Editors",
        )

        team_editor_permissions = Permission.objects.filter(
            codename__in=TEAM_EDITOR_PERMISSION_TYPES
        )
        team_editors.permissions.add(*team_editor_permissions)
        team_editors.save()
