from typing import Iterator

from django.db import models
from django.urls import reverse
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


class Person(models.Model):
    user = models.OneToOneField(
        "user.User", models.CASCADE, primary_key=True, related_name="profile"
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

    pronouns = models.CharField(max_length=16, null=True, blank=True)
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
    # TODO: Find out what the longest value in live is.
    primary_phone_number = models.CharField(
        "Preferred contact number",
        max_length=20,
        null=True,
        blank=True,
        help_text=(
            "Enter your preferred contact telephone number. Include your country"
            " dialling code."
        ),
    )
    secondary_phone_number = models.CharField(
        "Alternative contact number",
        max_length=20,
        null=True,
        blank=True,
        help_text=(
            "Enter an alternative contact telephone number. Include your country"
            " dialling code."
        ),
    )
    # TODO: Find out what the longest value in live is.
    town_city_or_region = models.CharField(
        "Town, city or region",
        max_length=50,
        null=True,
        blank=True,
        help_text="For example, London",
    )
    building = models.CharField(
        "Where do you usually work?", max_length=50, null=True, blank=True
    )
    regional_building = models.CharField(
        "UK regional building or location", max_length=50, null=True, blank=True
    )
    international_building = models.CharField(
        "International building or location", max_length=50, null=True, blank=True
    )
    location_in_building = models.CharField(
        "Where in the building do you work?",
        max_length=50,
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
        "What other skills do you have?", max_length=255, null=True, blank=True
    )
    fluent_languages = models.CharField(
        "Which languages do you speak fluently?",
        max_length=100,
        null=True,
        blank=True,
        help_text="Add languages that you are fluent in. Use a comma to separate languages.",
    )
    intermediate_languages = models.CharField(
        "Which other languages do you speak?",
        max_length=100,
        null=True,
        blank=True,
        help_text="Add languages that you speak but aren't fluent in. Use a comma to separate languages.",
    )
    other_learning_interests = models.CharField(
        "What other learning and development interests do you have?",
        max_length=255,
        null=True,
        blank=True,
    )
    other_additional_roles = models.CharField(
        "What other additional roles or responsibilities do you have?",
        max_length=255,
        null=True,
        blank=True,
    )
    previous_experience = models.TextField(
        "Previous positions I have held",
        null=True,
        blank=True,
        help_text="List where you have worked before your current role.",
    )
    photo = models.ImageField(
        max_length=255, null=True, blank=True, validators=[validate_virus_check_result]
    )

    def __str__(self) -> str:
        return self.user.get_full_name()

    def get_absolute_url(self) -> str:
        return reverse("profile-view", kwargs={"profile_pk": self.pk})

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
        unique=True,
        help_text="The full name of this team (e.g. Digital, Data and Technology)",
    )
    abbreviation = models.CharField(
        "Team acronym or initials",
        max_length=10,
        null=True,
        blank=True,
        help_text="A short form of the team name, up to 10 characters. For example DDaT.",
    )
    slug = models.SlugField(max_length=100)
    description = models.TextField(
        "Team description",
        null=False,
        blank=False,
        default=DEFAULT_TEAM_DESCRIPTION,
        help_text="What does this team do? Use Markdown to add lists and links. Enter up to 1500 characters.",
    )

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
    person = models.ForeignKey("Person", models.CASCADE, related_name="roles")
    team = models.ForeignKey("Team", models.CASCADE, related_name="members")

    job_title = models.CharField(max_length=100, blank=False)
    head_of_team = models.BooleanField(default=False)

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
