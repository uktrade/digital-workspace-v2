from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import (
    get_client,
    get_profile,
    has_valid_token,
)
from django.contrib.auth import get_user_model


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

        user.set_unusable_password()
        user.save()

        return user
