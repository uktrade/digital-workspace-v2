from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    sso_contact_email = models.EmailField(
        blank=True,
        null=True,
    )
    legacy_sso_user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
