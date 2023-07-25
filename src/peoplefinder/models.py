import uuid
from typing import Iterator

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg, StringAgg
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Case, F, Func, JSONField, Q, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils import timezone
from django_chunk_upload_handlers.clam_av import validate_virus_check_result

from wagtail.search.queryset import SearchableQuerySetMixin

from extended_search.index import Indexed
from extended_search.fields import IndexedField  # , RelatedIndexedFields
from extended_search.managers.index import ModelIndexManager

# United Kingdom
DEFAULT_COUNTRY_PK = "CTHMTC00260"


class WorkdayQuerySet(models.QuerySet):
    def all_mon_to_sun(self):
        codes = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

        return sorted(self.all(), key=lambda x: codes.index(x.code))


class Workday(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_workday_code"),
            models.UniqueConstraint(fields=["name"], name="unique_workday_name"),
        ]

    code = models.CharField(max_length=3)
    name = models.CharField(max_length=9)

    objects = WorkdayQuerySet.as_manager()

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


class NewNetwork(models.Model):
    page = models.OneToOneField("networks.Network", models.PROTECT)
    old_network = models.OneToOneField("Network", models.PROTECT, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.page)


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


class ActivePeopleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_active=False)


class PersonQuerySet(SearchableQuerySetMixin, models.QuerySet):
    def active(self):
        return self.exclude(is_active=False)

    def get_annotated(self):
        return self.annotate(
            formatted_roles=ArrayAgg(
                Concat(
                    "roles__job_title",
                    Value(" in "),
                    "roles__team__name",
                    Case(
                        When(roles__head_of_team=True, then=Value(" (head of team)")),
                        default=Value(""),
                    ),
                ),
                filter=Q(roles__isnull=False),
                distinct=True,
            ),
            formatted_buildings=StringAgg(
                "buildings__name",
                delimiter=", ",
                distinct=True,
            ),
            formatted_networks=StringAgg(
                "networks__name",
                delimiter=", ",
                distinct=True,
            ),
            formatted_additional_responsibilities=StringAgg(
                "additional_roles__name",
                delimiter=", ",
                distinct=True,
            ),
            formatted_key_skills=StringAgg(
                "key_skills__name",
                delimiter=", ",
                distinct=True,
            ),
            formatted_learning_and_development=StringAgg(
                "learning_interests__name",
                delimiter=", ",
                distinct=True,
            ),
            formatted_professions=StringAgg(
                "professions__name",
                delimiter=", ",
                distinct=True,
            ),
            workday_list=ArrayAgg(
                "workdays__code",
                distinct=True,
            ),
        )

    def get_search_query(self, query_str):  # @TODO is this the right place for this?
        return PersonIndexManager.get_search_query(query_str, self.model)


def person_photo_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/{filename}"


def person_photo_small_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/small_{filename}"


class PersonIndexManager(ModelIndexManager):
    fields = [
        IndexedField(
            "full_name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            boost=7.0,
        ),
        IndexedField(
            "email",
            keyword=True,
            boost=4.0,
        ),
        IndexedField(
            "contact_email",
            keyword=True,
            boost=4.0,
        ),
        IndexedField(
            "primary_phone_number",
            keyword=True,
            boost=4.0,
        ),
        IndexedField(
            "secondary_phone_number",
            keyword=True,
            boost=4.0,
        ),
        # Flattened relatedfields...
        IndexedField(
            "search_titles",
            tokenized=True,
            explicit=True,
            boost=3.0,
        ),
        IndexedField(
            "search_skills",
            tokenized=True,
        ),
        IndexedField(
            "search_interests",
            tokenized=True,
        ),
        IndexedField(
            "search_additional_roles",
            tokenized=True,
        ),
        IndexedField(
            "search_networks",
            tokenized=True,
        ),
        # RelatedIndexedFields(
        #     "roles",
        #     [
        #         IndexedField(
        #             "job_title",
        #             tokenized=True,
        #             explicit=True,
        #             boost=3.0,
        #         ),
        #     ],
        # ),
        # RelatedIndexedFields(
        #     "key_skills",
        #     [
        #         IndexedField(
        #             "name",
        #             tokenized=True,
        #             explicit=True,
        #             boost=0.8,
        #         ),
        #     ],
        # ),
        # RelatedIndexedFields(
        #     "learning_interests",
        #     [
        #         IndexedField(
        #             "name",
        #             tokenized=True,
        #             boost=0.8,
        #         ),
        #     ],
        # ),
        # RelatedIndexedFields(
        #     "additional_roles",
        #     [
        #         IndexedField(
        #             "name",
        #             tokenized=True,
        #             explicit=True,
        #             boost=0.8,
        #         ),
        #     ],
        # ),
        # RelatedIndexedFields(
        #     "networks",
        #     [
        #         IndexedField(
        #             "name",
        #             tokenized=True,
        #             explicit=True,
        #             filter=True,
        #             boost=1.5,
        #         ),
        #     ],
        # ),
        IndexedField(
            "town_city_or_region",
            tokenized=True,
            boost=1.5,
        ),
        IndexedField(
            "regional_building",
            tokenized=True,
        ),
        IndexedField(
            "international_building",
            tokenized=True,
        ),
        IndexedField(
            "fluent_languages",
            tokenized=True,
            boost=1.5,
        ),
        IndexedField(
            "search_teams",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=2.0,
        ),
        IndexedField(
            "has_photo",
            proximity=True,
            boost=1.5,
        ),
        IndexedField(
            "profile_completion",
            proximity=True,
            boost=2.0,
        ),
        IndexedField(
            "is_active",
            filter=True,
        ),
        IndexedField(
            "professions",
            filter=True,
        ),
        IndexedField(
            "grade",
            filter=True,
        ),
        IndexedField(
            "networks",
            filter=True,
        ),
        IndexedField("do_not_work_for_dit", filter=True),
    ]


class Person(Indexed, models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(id=F("manager")), name="manager_cannot_be_self"
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
        "countries.Country",
        models.PROTECT,
        default=DEFAULT_COUNTRY_PK,
        related_name="+",
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
    # Used for matching new users with existing profiles.
    legacy_sso_user_id = models.CharField(max_length=255, null=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_or_confirmed_at = models.DateTimeField(default=timezone.now)

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
        "My manager is not listed because I do not work for DBT", default=False
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
        max_length=200,
        null=True,
        blank=True,
        help_text="Enter languages that you are fluent in. Use a comma to separate them.",
    )
    intermediate_languages = models.CharField(
        "Which other languages do you speak?",
        max_length=200,
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
    login_count = models.IntegerField(default=0)
    profile_completion = models.IntegerField(default=0)

    objects = models.Manager.from_queryset(PersonQuerySet)()
    active = ActivePeopleManager.from_queryset(PersonQuerySet)()

    search_fields = PersonIndexManager()

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
        return (timezone.now() - self.edited_or_confirmed_at).days >= 365

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def preferred_email(self) -> str:
        return self.contact_email or self.email

    @property
    def all_languages(self) -> str:
        return ", ".join(
            filter(None, [self.fluent_languages, self.intermediate_languages])
        )

    @property
    def has_photo(self) -> bool:
        return bool(self.photo)

    @property
    def search_teams(self):
        """
        Indexable string of team names and abbreviations
        """
        teams = self.roles.all()
        names = teams.values_list("team__name", flat=True)
        names_str = " ".join(list([n or "" for n in names]))
        abbrs = teams.values_list("team__abbreviation", flat=True)
        abbrs_str = " ".join(list([a or "" for a in abbrs]))
        return f"{names_str} {abbrs_str}"

    @property
    def search_titles(self):
        return ", ".join(self.roles.all().values_list("job_title", flat=True))

    @property
    def search_skills(self):
        return ", ".join(self.key_skills.all().values_list("name", flat=True))

    @property
    def search_interests(self):
        return ", ".join(self.learning_interests.all().values_list("name", flat=True))

    @property
    def search_additional_roles(self):
        return ", ".join(self.additional_roles.all().values_list("name", flat=True))

    @property
    def search_networks(self):
        return ", ".join(self.networks.all().values_list("name", flat=True))

    def get_workdays_display(self) -> str:
        workdays = self.workdays.all_mon_to_sun()

        workday_codes = [x.code for x in workdays]
        mon_to_fri_codes = ["mon", "tue", "wed", "thu", "fri"]

        # "Monday to Friday"
        if workday_codes == mon_to_fri_codes:
            return f"{workdays[0]} to {workdays[-1]}"

        # "Monday, Tuesday, Wednesday, ..."
        return ", ".join(map(str, workdays))

    def save(self, *args, **kwargs):
        from peoplefinder.services.person import PersonService

        self.profile_completion = PersonService().get_profile_completion(person=self)
        return super().save(*args, **kwargs)


class TeamQuerySet(SearchableQuerySetMixin, models.QuerySet):
    def with_all_parents(self):
        return self.annotate(
            all_parents=ArrayAgg(
                Func(
                    Value("slug"),
                    "children__parent__slug",
                    Value("short_name"),
                    # Replicate `Team.short_name` behaviour.
                    Case(
                        When(
                            children__parent__abbreviation__isnull=False,
                            then=F("children__parent__abbreviation"),
                        ),
                        default=F("children__parent__name"),
                    ),
                    function="jsonb_build_object",
                    output_field=JSONField(),
                ),
                # Filter out the last team (deepest).
                filter=~Q(children__parent=F("pk")),
                ordering="-children__depth",
            ),
        )

    def with_parents(self, parent_field: str = "pk"):
        """Annotate the queryset with an array of parent values.

        Notes:
            - annotated field is `ancestry`
            - array will include the value from the team itself
            - values are determined by the `parent_field` argument

        Examples:
            With the default `parent_field`:
            >>> team = Team.objects.with_parents().get(slug="software")
            >>> team.ancestry
            [1, 3, 4]

            With a specified `parent_field`:
            >>> team = Team.objects.with_parents(parent_field="slug").get(slug="software")
            >>> team.ancestry
            ['spacex', 'engineering', 'software']

        Args:
            parent_field: The parent field to populate the array with.
        """
        return self.annotate(
            ancestry=ArrayAgg(
                f"children__parent__{parent_field}",
                ordering="-children__depth",
            )
        )

    def get_search_query(self, query_str):  # @TODO is this the right place for this?
        return TeamIndexManager.get_search_query(query_str, self.model)


class TeamIndexManager(ModelIndexManager):
    fields = [
        IndexedField(
            "name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            boost=4.0,
        ),
        IndexedField(
            "abbreviation",
            tokenized=True,
            explicit=True,
            keyword=True,
            boost=4.0,
        ),
        IndexedField(
            "description",
            tokenized=True,
            explicit=True,
        ),
        IndexedField(
            "roles_in_team",
            tokenized=True,
            explicit=True,
            boost=2.0,
        ),
    ]


# markdown
DEFAULT_TEAM_DESCRIPTION = """Find out who is in the team and their contact details.

You can update this description, by [updating your team information](https://workspace.trade.gov.uk/working-at-dbt/how-do-i/update-my-team-information-on-people-finder/).
"""


class Team(Indexed, models.Model):
    class LeadersOrdering(models.TextChoices):
        ALPHABETICAL = "alphabetical", "Alphabetical"
        CUSTOM = "custom", "Custom"

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
    slug = models.SlugField(max_length=130, unique=True, editable=True)
    description = models.TextField(
        "Team description",
        null=False,
        blank=False,
        default=DEFAULT_TEAM_DESCRIPTION,
        help_text="What does this team do? Use Markdown to add lists and links. Enter up to 1500 characters.",
    )
    leaders_ordering = models.CharField(
        max_length=12,
        choices=LeadersOrdering.choices,
        default=LeadersOrdering.ALPHABETICAL,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TeamQuerySet.as_manager()
    search_fields = TeamIndexManager()

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
        order_by = []

        if self.leaders_ordering == self.LeadersOrdering.CUSTOM:
            order_by.append("leaders_position")

        order_by += ["person__last_name", "person__first_name"]

        yield from self.members.active().filter(head_of_team=True).order_by(*order_by)

    @property
    def roles_in_team(self) -> list[str]:
        return list(
            TeamMember.objects.filter(team=self).values_list("job_title", flat=True)
        )


class ActiveTeamMemberManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(person__is_active=False)


class TeamMemberQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(person__is_active=False)


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
    leaders_position = models.SmallIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(TeamMemberQuerySet)()
    active = ActiveTeamMemberManager.from_queryset(TeamMemberQuerySet)()

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
