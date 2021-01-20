from django.contrib.auth import get_user_model
from django.db.models import Q

from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import (
    get_client,
    get_profile,
    has_valid_token,
)


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.get_or_create_user(profile)
        return None

    @staticmethod
    def get_or_create_user(profile):
        User = get_user_model()

        user = User.objects.filter(
            Q(
                email=profile["user_id"]
            ) | Q(
                username=profile["user_id"]
            ) | Q(
                username=profile["email_user_id"]
            )
        ).first()

        if user:
            # Set email_user_id as username (it is now the preferred option)
            user.username = profile["email_user_id"]
            user.email = profile["email"]  # might change over time
            user.sso_contact_email = profile["contact_email"]  # might change over time
            user.first_name = profile["first_name"]  # might change over time
            user.last_name = profile["last_name"]  # might change over time
        else:
            user = User(
                username=profile["email_user_id"],
                email=profile["email"],
                sso_contact_email=profile["contact_email"],
                first_name=profile["first_name"],
                last_name=profile["last_name"],
            )

        user.set_unusable_password()
        user.save()

        return user
