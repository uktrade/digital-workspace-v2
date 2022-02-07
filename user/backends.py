from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import (
    get_client,
    get_profile,
    has_valid_token,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from peoplefinder.services.person import PersonService


User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.get_or_create_user(profile)
        return None

    @staticmethod
    def get_or_create_user(profile):
        users_matching_sso_record = User.objects.filter(
            username=profile["email_user_id"]
        )

        # There can only be 0 users or 1 match
        assert (  # noqa S101
            users_matching_sso_record.count() < 2
        ), "Duplicate email SSO id user found"
        user = users_matching_sso_record.first()

        if user:
            # Set email_user_id as username (it is now the preferred option)
            user.username = profile["email_user_id"]
            user.email = profile["email"]  # might change over time
            user.sso_contact_email = profile["contact_email"]  # might change over time
            user.first_name = profile["first_name"]  # might change over time
            user.last_name = profile["last_name"]  # might change over time
            user.legacy_sso_user_id = profile["user_id"]
        else:
            user = User(
                username=profile["email_user_id"],
                email=profile["email"],
                sso_contact_email=profile["contact_email"],
                first_name=profile["first_name"],
                last_name=profile["last_name"],
                legacy_sso_user_id=profile["user_id"],
            )

        # TODO - discuss below with SD
        # Add edit profile permission
        # edit_profile_permission = Permission.objects.get(codename='edit_profile')
        # user.user_permissions.add(edit_profile_permission)

        user.set_unusable_password()
        user.save()

        # Add group with edit profile permission
        edit_profile_group = Group.objects.get(name="Profile Editors")
        user.groups.add(edit_profile_group)

        PersonService().create_user_profile(user)

        return user
