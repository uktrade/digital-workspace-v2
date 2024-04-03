from django.conf import settings
from django.db import models
from wagtail.models import Page


class IntranetProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="intranet",
    )
    bookmarks = models.ManyToManyField(
        Page,
        through="Bookmark",
        through_fields=("profile", "page"),
        related_name="+",
    )
    recent_page_views = models.ManyToManyField(
        Page,
        through="RecentPageView",
        through_fields=("profile", "page"),
        related_name="+",
    )


# Through model
class Bookmark(models.Model):
    profile = models.ForeignKey(
        IntranetProfile,
        on_delete=models.CASCADE,
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
    )


# Through model
class RecentPageView(models.Model):
    class Meta:
        ordering = ["-last_viewed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "page"], name="unique_recent_page_view"
            )
        ]

    profile = models.ForeignKey(
        IntranetProfile,
        on_delete=models.CASCADE,
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
    )
    last_viewed_at = models.DateTimeField(auto_now=True)
