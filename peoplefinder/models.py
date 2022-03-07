import uuid
from typing import Iterator

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Case, Exists, F, OuterRef, Q, When
from django.urls import reverse
from django.utils import timezone
from django_chunk_upload_handlers.clam_av import validate_virus_check_result


# TODO: django doesnt support on update cascade and it's possible that a code
# might change in the future so we should probably change this to use an id
# column.
class Country(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_country_code"),
            models.UniqueConstraint(fields=["name"], name="unique_country_name"),
        ]
        ordering = ["name"]

    DEFAULT_CODE = "GB"

    code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_default_id(cls):
        return Country.objects.get(code=cls.DEFAULT_CODE).id


class Workday(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_workday_code"),
            models.UniqueConstraint(fields=["name"], name="unique_workday_name"),
        ]

    code = models.CharField(max_length=3)
    name = models.CharField(max_length=9)

    def __str__(self) -> str:
        return self.name


class Grade(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_grade_code"),
            models.UniqueConstraint(fields=["name"], name="unique_grade_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class KeySkill(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_key_skill_code"),
            models.UniqueConstraint(fields=["name"], name="unique_key_skill_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class LearningInterest(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"], name="unique_learning_interest_code"
            ),
            models.UniqueConstraint(
                fields=["name"], name="unique_learning_interest_name"
            ),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Network(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_network_code"),
            models.UniqueConstraint(fields=["name"], name="unique_network_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Profession(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_profession_code"),
            models.UniqueConstraint(fields=["name"], name="unique_profession_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=60)

    def __str__(self) -> str:
        return self.name


class AdditionalRole(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"], name="unique_additional_role_code"
            ),
            models.UniqueConstraint(
                fields=["name"], name="unique_additional_role_name"
            ),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=40)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Building(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_building_code"),
            models.UniqueConstraint(fields=["name"], name="unique_building_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=40)

    def __str__(self) -> str:
        return self.name


# We have excluded any person with is_active=False, as this means that
# they have left the organisation. If we ever require a queryset with
# inactive users, refactoring will be necessary.
class PersonManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_active=False)


class PersonQuerySet(models.QuerySet):
    def with_profile_completion(self):
        # Each statement in this list should return 0 or 1 to represent whether that
        # field is complete.
        fields = [
            Case(When(country__isnull=False, then=1), default=0),
            Case(When(town_city_or_region__isnull=False, then=1), default=0),
            Case(When(primary_phone_number__isnull=False, then=1), default=0),
            Case(When(manager__isnull=False, then=1), default=0),
            Case(When(photo__isnull=False, then=1), default=0),
            Case(When(user__email__isnull=False, then=1), default=0),
            Case(When(user__first_name__isnull=False, then=1), default=0),
            Case(When(user__last_name__isnull=False, then=1), default=0),
            Case(
                When(
                    Exists(TeamMember.objects.filter(person_id=OuterRef("user_id"))),
                    then=1,
                ),
                default=0,
            ),
        ]

        # `sum(fields)` is the same as doing `fields[0] + field[1] + field[2]`.
        # This will create a SQL query which will add up the completed fields.
        completed = sum(fields)
        # We need the `total` as a float so that the SQL calculates the decimal
        # percentage correctly.
        total = float(len(fields))

        return self.annotate(profile_completion=(completed / total) * 100)


def person_photo_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/{filename}"


def person_photo_small_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/small_{filename}"


class Person(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(pk=F("manager")), name="manager_cannot_be_self"
            ),
        ]

    is_active = models.BooleanField(default=True)
    became_inactive = models.DateTimeField(null=True, blank=True)
    user = models.OneToOneField(
        "user.User", models.CASCADE, null=True, blank=True, related_name="profile"
    )
    manager = models.ForeignKey(
        "Person", models.SET_NULL, null=True, blank=True, related_name="+"
    )
    country = models.ForeignKey(
        "Country", models.SET_DEFAULT, default=Country.get_default_id, related_name="+"
    )
    workdays = models.ManyToManyField(
        "Workday",
        verbose_name="Which days do you usually work?",
        blank=True,
        related_name="+",
    )
    grade = models.ForeignKey(
        "Grade", models.SET_NULL, null=True, blank=True, related_name="+"
    )
    key_skills = models.ManyToManyField(
        "KeySkill",
        verbose_name="What are your skills?",
        blank=True,
        related_name="+",
        help_text="Select all that apply",
    )
    learning_interests = models.ManyToManyField(
        "LearningInterest",
        verbose_name="What are your learning and development interests?",
        blank=True,
        related_name="+",
        help_text="Select all that apply",
    )
    networks = models.ManyToManyField(
        "Network",
        verbose_name="What networks do you belong to?",
        blank=True,
        related_name="+",
        help_text="Select all that apply",
    )
    professions = models.ManyToManyField(
        "Profession",
        verbose_name="What professions do you belong to?",
        blank=True,
        related_name="+",
        help_text="Select all that apply",
    )
    additional_roles = models.ManyToManyField(
        "AdditionalRole",
        verbose_name="Do you have any additional roles or responsibilities?",
        blank=True,
        related_name="+",
        help_text="Select all that apply",
    )
    buildings = models.ManyToManyField(
        "Building",
        verbose_name="Where do you usually work?",
        blank=True,
        related_name="+",
    )

    slug = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    legacy_slug = models.CharField(
        unique=True, max_length=80, null=True, editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(
        "Main work email address",
        help_text=(
            "Enter your own official work email address provided by the"
            " organisation you are directly employed by or contracted to."
        ),
    )
    pronouns = models.CharField(max_length=40, null=True, blank=True)
    contact_email = models.EmailField(
        "Contact email address",
        null=True,
        blank=True,
        help_text=(
            "Enter the email address your colleagues should contact you on, for"
            " example, a jobshare or Private Office mailbox. This will be shown on your"
            " profile instead of your main work email address. Do not enter a personal"
            " email address, or a work email address that is not safe for official"
            " information."
        ),
    )
    primary_phone_number = models.CharField(
        "Preferred contact number",
        max_length=42,
        null=True,
        blank=True,
        help_text=(
            "Enter your preferred contact telephone number. Include your country"
            " dialling code."
        ),
    )
    secondary_phone_number = models.CharField(
        "Alternative contact number",
        max_length=160,
        null=True,
        blank=True,
        help_text=(
            "Enter an alternative contact telephone number. Include your country"
            " dialling code."
        ),
    )
    town_city_or_region = models.CharField(
        "Town, city or region",
        max_length=78,
        null=True,
        blank=True,
        help_text="For example, London",
    )
    regional_building = models.CharField(
        "UK regional building or location", max_length=130, null=True, blank=True
    )
    international_building = models.CharField(
        "International building or location", max_length=110, null=True, blank=True
    )
    location_in_building = models.CharField(
        "Where in the building do you work?",
        max_length=130,
        null=True,
        blank=True,
        help_text=(
            "Skip this question if you work in a Foreign and Commonwealth Office (FCO)"
            " building"
        ),
    )
    do_not_work_for_dit = models.BooleanField(
        "My manager is not listed because I do not work for DIT", default=False
    )
    other_key_skills = models.CharField(
        "What other skills do you have?",
        max_length=700,
        null=True,
        blank=True,
        help_text="Enter your skills. Use a comma to separate them.",
    )
    fluent_languages = models.CharField(
        "Which languages do you speak fluently?",
        max_length=100,
        null=True,
        blank=True,
        help_text="Enter languages that you are fluent in. Use a comma to separate them.",
    )
    intermediate_languages = models.CharField(
        "Which other languages do you speak?",
        max_length=130,
        null=True,
        blank=True,
        help_text="Enter languages that you speak but aren't fluent in. Use a comma to separate them.",
    )
    other_learning_interests = models.CharField(
        "What other learning and development interests do you have?",
        max_length=255,
        null=True,
        blank=True,
        help_text="Enter your interests. Use a comma to separate them.",
    )
    other_additional_roles = models.CharField(
        "What other additional roles or responsibilities do you have?",
        max_length=400,
        null=True,
        blank=True,
        help_text="Enter your roles or responsibilities. Use a comma to separate them.",
    )
    previous_experience = models.TextField(
        "Previous positions I have held",
        null=True,
        blank=True,
        help_text="List where you have worked before your current role.",
    )
    photo = models.ImageField(
        max_length=255,
        null=True,
        blank=True,
        upload_to=person_photo_path,
        validators=[validate_virus_check_result],
    )
    photo_small = models.ImageField(
        max_length=255,
        null=True,
        blank=True,
        upload_to=person_photo_small_path,
        validators=[validate_virus_check_result],
    )

    objects = PersonManager.from_queryset(PersonQuerySet)()

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("profile-view", kwargs={"profile_slug": self.slug})

    def get_all_key_skills(self) -> Iterator[str]:
        yield from self.key_skills.all()

        if self.other_key_skills:
            yield self.other_key_skills

    def get_all_learning_interests(self) -> Iterator[str]:
        yield from self.learning_interests.all()

        if self.other_learning_interests:
            yield self.other_learning_interests

    def get_all_additional_roles(self) -> Iterator[str]:
        yield from self.additional_roles.all()

        if self.other_additional_roles:
            yield self.other_additional_roles

    @property
    def is_stale(self):
        return (timezone.now() - self.updated_at).days >= 365

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def preferred_email(self):
        return self.contact_email or self.email


# markdown
DEFAULT_TEAM_DESCRIPTION = """Find out who is in the team and their contact details.

You can update this description, by [updating your team information](https://workspace.trade.gov.uk/working-at-dit/how-do-i/update-my-team-information-on-people-finder/).
"""


class Team(models.Model):
    people = models.ManyToManyField(
        "Person", through="TeamMember", related_name="teams"
    )

    name = models.CharField(
        "Team name (required)",
        max_length=255,
        help_text="The full name of this team (e.g. Digital, Data and Technology)",
    )
    abbreviation = models.CharField(
        "Team acronym or initials",
        max_length=20,
        null=True,
        blank=True,
        help_text="A short form of the team name, up to 10 characters. For example DDaT.",
    )
    slug = models.SlugField(max_length=130, unique=True, editable=False)
    description = models.TextField(
        "Team description",
        null=False,
        blank=False,
        default=DEFAULT_TEAM_DESCRIPTION,
        help_text="What does this team do? Use Markdown to add lists and links. Enter up to 1500 characters.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.short_name

    def get_absolute_url(self) -> str:
        return reverse("team-view", kwargs={"slug": self.slug})

    @property
    def short_name(self) -> str:
        """Return a short name for the team.

        Returns:
            str: The team's short name.
        """
        return self.abbreviation or self.name

    @property
    def leaders(self):
        yield from self.members.filter(head_of_team=True)


class TeamMember(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "team", "job_title", "head_of_team"],
                name="unique_team_member",
            ),
        ]

    person = models.ForeignKey("Person", models.CASCADE, related_name="roles")
    team = models.ForeignKey("Team", models.CASCADE, related_name="members")

    job_title = models.CharField(
        max_length=255, help_text="Enter your role in this team"
    )
    head_of_team = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.team} - {self.person}"


class TeamTree(models.Model):
    class Meta:
        unique_together = [["parent", "child"]]

    parent = models.ForeignKey("Team", models.CASCADE, related_name="parents")
    child = models.ForeignKey("Team", models.CASCADE, related_name="children")

    depth = models.SmallIntegerField()

    def __str__(self) -> str:
        return f"{self.parent} - {self.child} ({self.depth})"


class AuditLog(models.Model):
    class Meta:
        ordering = ["timestamp"]
        get_latest_by = "timestamp"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"

    action = models.CharField(max_length=6, choices=Action.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    object_repr = models.JSONField(encoder=DjangoJSONEncoder)
    diff = models.JSONField(encoder=DjangoJSONEncoder)


# NOTE: This model is read-only!
class LegacyAuditLog(models.Model):
    class Meta:
        ordering = ["timestamp"]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"

    action = models.CharField(max_length=6, choices=Action.choices)
    automated = models.BooleanField()
    timestamp = models.DateTimeField()
    object = models.TextField(null=True)
    object_changes = models.TextField(null=True)

    def save(self, *args, **kwargs):
        return

    def delete(self, *args, **kwargs):
        return
