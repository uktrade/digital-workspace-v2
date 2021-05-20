from django.db import models
from django.urls import reverse


# TODO: django doesnt support on update cascade and it's possible that a code
# might change in the future so we should probably change this to use an id
# column.
class Country(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_country_code"),
            models.UniqueConstraint(fields=["name"], name="unique_country_name"),
        ]

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

    code = models.CharField(max_length=30)
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
    do_not_work_for_dit = models.BooleanField(
        "My manager is not listed because I do not work for DIT", default=False
    )

    def __str__(self) -> str:
        return self.user.get_full_name()

    def get_absolute_url(self) -> str:
        return reverse("profile-view", kwargs={"profile_pk": self.pk})


class Team(models.Model):
    people = models.ManyToManyField(
        "Person", through="TeamMember", related_name="teams"
    )

    name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=10, null=True, blank=True)
    slug = models.SlugField(max_length=100)

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
