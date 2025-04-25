from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history import register

from core import field_models


class User(AbstractUser):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["legacy_sso_user_id"], name="unique_legacy_sso_user_id"
            ),
        ]

    sso_contact_email = models.EmailField(
        blank=True,
        null=True,
    )
    legacy_sso_user_id = field_models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


register(User)
