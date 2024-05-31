from django.conf import settings
from django.db import models
from wagtail.models import Page


class UserPage(models.Model):
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "page"], name="unique_%(app_label)s_%(class)s"
            )
        ]
        ordering = ["-updated_at"]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Bookmark(UserPage):
    pass


class RecentPageView(UserPage):
    count = models.PositiveIntegerField(default=1)
