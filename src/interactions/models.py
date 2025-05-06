from django.conf import settings
from django.db import models
from wagtail.models import Page

from core import field_models
from news.models import Comment


class UserObject(models.Model):
    class Meta:
        abstract = True
        ordering = ["-updated_at"]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserPage(UserObject):
    class Meta(UserObject.Meta):
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "page"], name="unique_%(app_label)s_%(class)s"
            )
        ]

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
    )


class UserComment(UserObject):
    class Meta(UserObject.Meta):
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comment"], name="unique_%(app_label)s_%(class)s"
            )
        ]

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
    )


class Bookmark(UserPage):
    pass


class RecentPageView(UserPage):
    count = models.PositiveIntegerField(default=1)


class ReactionType(models.TextChoices):
    CELEBRATE = "celebrate", "Celebrate"
    LIKE = "like", "Like"
    LOVE = "love", "Love"
    DISLIKE = "dislike", "Dislike"
    UNHAPPY = "unhappy", "Unhappy"


class PageReaction(UserPage):
    type = field_models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        verbose_name="Reaction Type",
        help_text="Select the type of reaction (e.g., Like or Dislike).",
    )


class CommentReaction(UserComment):
    type = field_models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        verbose_name="Reaction Type",
        help_text="Select the type of reaction (e.g., Like or Dislike).",
    )
