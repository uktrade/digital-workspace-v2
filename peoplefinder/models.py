from django.db import models
from django.urls import reverse


class Country(models.Model):
    DEFAULT_CODE = "GB"

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Workday(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=9)

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
        "Country", models.SET_DEFAULT, default=Country.DEFAULT_CODE, related_name="+"
    )
    workdays = models.ManyToManyField("Workday", blank=True)

    pronouns = models.CharField(max_length=16, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    # TODO: Find out what the longest value in live is.
    primary_phone_number = models.CharField(max_length=20, null=True, blank=True)
    secondary_phone_number = models.CharField(max_length=20, null=True, blank=True)
    # TODO: Find out what the longest value in live is.
    town_city_or_region = models.CharField(max_length=50, null=True, blank=True)
    building = models.CharField(max_length=50, null=True, blank=True)
    regional_building = models.CharField(max_length=50, null=True, blank=True)
    international_building = models.CharField(max_length=50, null=True, blank=True)
    location_in_building = models.CharField(max_length=50, null=True, blank=True)

    do_not_work_for_dit = models.BooleanField(default=False)

    def get_absolute_url(self) -> str:
        return reverse("profile-view", kwargs={"pk": self.pk})


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

    job_title = models.CharField(max_length=100)
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
