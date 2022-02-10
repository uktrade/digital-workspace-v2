from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


PROFILE_EDITOR_PERMISSION_TYPES = [
    "edit_profile",
]

PERSON_EDITOR_PERMISSION_TYPES = [
    "edit_profile",
    "delete_profile",
]

TEAM_EDITOR_PERMISSION_TYPES = [
    "add_team",
    "change_team",
    "delete_team",
]


class Command(BaseCommand):
    help = "Create page permissions"

    def handle(self, *args, **options):
        user_editors, _ = Group.objects.get_or_create(
            name="Profile Editors",
        )

        user_editor_permissions = Permission.objects.filter(
            codename__in=PROFILE_EDITOR_PERMISSION_TYPES
        )
        user_editors.permissions.add(*user_editor_permissions)
        user_editors.save()

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
