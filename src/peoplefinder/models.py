import datetime
import uuid
from typing import Iterator, Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg, StringAgg
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Case, F, Func, JSONField, Q, Value, When
from django.db.models.functions import Concat
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe  # noqa: S308
from django_chunk_upload_handlers.clam_av import validate_virus_check_result
from wagtail.search.queryset import SearchableQuerySetMixin

from core.models import IngestedModel
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed, RelatedFields, ScoreFunction


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
        ordering = ["ordering"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    ordering = models.IntegerField(null=True, blank=True)

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


class Network(Indexed, models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_network_code"),
            models.UniqueConstraint(fields=["name"], name="unique_network_name"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)

    indexed_fields = [
        IndexedField(
            "name",
            tokenized=True,
            explicit=True,
            fuzzy=True,
        ),
    ]

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


class UkStaffLocation(IngestedModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_location_code"),
        ]
        ordering = ["name"]

    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    organisation = models.CharField(max_length=255)
    building_name = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.name


class ActivePeopleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_active=False)


class PersonQuerySet(SearchableQuerySetMixin, models.QuerySet):
    def active(self):
        return self.exclude(is_active=False)

    def active_or_inactive_within(self, *, days: int):
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        return self.exclude(became_inactive__lt=cutoff)

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


def person_photo_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/{filename}"


def person_photo_small_path(instance, filename):
    return f"peoplefinder/person/{instance.slug}/photo/small_{filename}"


class Person(Indexed, models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(id=F("manager")), name="manager_cannot_be_self"
            ),
        ]
        permissions = [
            ("can_view_inactive_profiles", "Can view inactive profiles"),
        ]
        ordering = ["grade", "first_name", "last_name"]

    is_active = models.BooleanField(default=True)
    became_inactive = models.DateTimeField(null=True, blank=True)
    user = models.OneToOneField(
        "user.User", models.CASCADE, null=True, blank=True, related_name="profile"
    )
    manager = models.ForeignKey(
        "Person", models.SET_NULL, null=True, blank=True, related_name="direct_reports"
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
    buildings.system_check_deprecated_details = {
        "msg": ("Person.buildings been deprecated."),
        "hint": "Use Person.uk_office_location and Person.remote_working instead.",
        "id": "peoplefinder.Person.E001",
    }
    uk_office_location = models.ForeignKey(
        "UkStaffLocation",
        verbose_name="What is your office location?",
        help_text="Your base location as per your contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class RemoteWorking(models.TextChoices):
        OFFICE_WORKER = (
            "office_worker",
            "I work primarily from the office",
        )
        REMOTE_WORKER = (
            "remote_worker",
            "I work primarily from home (remote worker)",
        )
        SPLIT = (
            "split",
            "I split my time between home and the office",
        )

    remote_working = models.CharField(
        verbose_name="Where do you usually work?",
        blank=True,
        null=True,
        max_length=80,
        choices=RemoteWorking.choices,
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

    first_name = models.CharField(
        max_length=200,
        help_text=(
            "If you enter a preferred name below, this name will be hidden to others"
        ),
    )
    preferred_first_name = models.CharField(
        max_length=200,
        help_text=(
            "This name appears on your profile. Colleagues can search for you"
            " using either of your first names"
        ),
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        max_length=200,
    )
    email = models.EmailField(
        "How we contact you",
        help_text="We will send Digital Workspace notifications to this email",
    )
    pronouns = models.CharField(max_length=40, null=True, blank=True)
    name_pronunciation = models.CharField(
        "How to pronounce your full name",
        help_text=mark_safe(  # noqa: S308
            "A phonetic representation of your name<br><a class='govuk-link' href='/news-and-views/say-my-name/' target='_blank' rel='noreferrer'>"
            "Tips for writing your name phonetically</a>"
        ),
        max_length=200,
        null=True,
        blank=True,
    )
    contact_email = models.EmailField(
        "Email address",
        null=True,
        blank=True,
        help_text="The work email you want people to contact you on",
    )
    primary_phone_number = models.CharField(
        "Phone number",
        max_length=42,
        null=True,
        blank=True,
        help_text=(
            "Enter the country's dialling code in place of the first 0. The"
            " UK's dialling code is +44."
        ),
    )
    secondary_phone_number = models.CharField(
        "Alternative phone number",
        max_length=160,
        null=True,
        blank=True,
        help_text=(
            "Enter the country's dialling code in place of the first 0. The"
            " UK's dialling code is +44."
        ),
    )
    town_city_or_region = models.CharField(
        "Town, city or region",
        max_length=78,
        null=True,
        blank=True,
        help_text="For example, London",
    )
    town_city_or_region.system_check_deprecated_details = {
        "msg": ("Person.town_city_or_region been deprecated."),
        "hint": "Use Person.uk_office_location",
        "id": "peoplefinder.Person.E001",
    }
    regional_building = models.CharField(
        "UK regional building or location",
        max_length=130,
        null=True,
        blank=True,
    )
    regional_building.system_check_deprecated_details = {
        "msg": ("Person.regional_building been deprecated."),
        "hint": "Use Person.uk_office_location and Person.remote_working instead.",
        "id": "peoplefinder.Person.E001",
    }
    usual_office_days = models.CharField(
        "What days do you usually come in to the office?",
        help_text=("For example: I usually come in on Mondays and Wednesdays"),
        max_length=200,
        null=True,
        blank=True,
    )
    international_building = models.CharField(
        "International location",
        max_length=110,
        null=True,
        blank=True,
        help_text="Complete if you work outside the UK",
    )
    location_in_building = models.CharField(
        "Location in the building",
        max_length=130,
        null=True,
        blank=True,
        help_text="If you sit in a particular area, you can let colleagues know here",
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
        "Which languages are you fluent in?",
        max_length=200,
        null=True,
        blank=True,
        help_text="Use a comma to separate the languages. For example: French, Polish, Ukrainian",
    )
    intermediate_languages = models.CharField(
        "Which other languages do you speak?",
        max_length=200,
        null=True,
        blank=True,
        help_text="These are languages you speak and write but are not fluent in",
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
        help_text="List where you have worked before your current role",
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
    ical_token = models.CharField(
        verbose_name="Individual token for iCal feeds",
        blank=True,
        null=True,
        max_length=80,
    )

    objects = models.Manager.from_queryset(PersonQuerySet)()
    active = ActivePeopleManager.from_queryset(PersonQuerySet)()

    indexed_fields = [
        IndexedField(
            "full_name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            boost=7.0,
        ),
        IndexedField(
            "first_name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            boost=7.0,
        ),
        IndexedField(
            "preferred_first_name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            boost=7.0,
        ),
        IndexedField(
            "last_name",
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
        IndexedField(
            "search_grade",
            explicit=True,
        ),
        IndexedField(
            "search_buildings",
            tokenized=True,
        ),
        IndexedField(
            "search_job_titles",
            tokenized=True,
            explicit=True,
            boost=3.0,
        ),
        RelatedFields(
            "roles",
            [
                IndexedField(
                    "job_title",
                    tokenized=True,
                    explicit=True,
                    boost=3.0,
                ),
            ],
        ),
        RelatedFields(
            "key_skills",
            [
                IndexedField(
                    "name",
                    tokenized=True,
                    explicit=True,
                    boost=0.8,
                ),
            ],
        ),
        IndexedField(
            "other_key_skills",
            tokenized=True,
            explicit=True,
            boost=0.8,
        ),
        RelatedFields(
            "learning_interests",
            [
                IndexedField(
                    "name",
                    tokenized=True,
                    boost=0.8,
                ),
            ],
        ),
        RelatedFields(
            "additional_roles",
            [
                IndexedField(
                    "name",
                    tokenized=True,
                    explicit=True,
                    boost=0.8,
                ),
            ],
        ),
        RelatedFields(
            "networks",
            [
                IndexedField(
                    "name",
                    tokenized=True,
                    explicit=True,
                    filter=True,
                    boost=1.5,
                ),
            ],
        ),
        IndexedField(
            "international_building",
            tokenized=True,
        ),
        IndexedField(
            "search_location",
            tokenized=True,
        ),
        IndexedField(
            "fluent_languages",
            tokenized=True,
        ),
        IndexedField(
            "search_teams",
            tokenized=True,
            explicit=True,
            boost=2.0,
        ),
        IndexedField(
            "has_photo",
            proximity=True,
            boost=1.5,
        ),
        ScoreFunction(
            "linear",
            field_name="profile_completion",
            origin=100,
            offset=5,
            scale=50,
            decay=0.95,
        ),
        IndexedField(
            "is_active",
            filter=True,
        ),
        IndexedField(
            "became_inactive",
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

    search_fields = []

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
        first_name = self.get_first_name_display()
        return f"{first_name} {self.last_name}"

    @property
    def preferred_email(self) -> str:
        return self.contact_email or self.email

    @property
    def is_line_manager(self) -> bool:
        return self.direct_reports.exists()

    @property
    def all_languages(self) -> str:
        return ", ".join(
            filter(None, [self.fluent_languages, self.intermediate_languages])
        )

    @property
    def has_photo(self) -> bool:
        return bool(self.photo)

    def days_since_account_creation(self) -> int:
        period = timezone.now() - self.created_at
        return period.days

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
    def search_job_titles(self):
        """
        Indexable string of job titles
        """
        job_titles = self.roles.all().values_list("job_title", flat=True)
        return " ".join(job_titles)

    @property
    def search_buildings(self):
        return ", ".join(self.buildings.all().values_list("name", flat=True))

    @property
    def search_location(self):
        if not self.uk_office_location:
            return None

        # The `name` usually includes the city.
        return self.uk_office_location.name

    @property
    def search_grade(self):
        return self.get_grade_display()

    def save(self, *args, **kwargs):
        from peoplefinder.services.person import PersonService

        self.profile_completion = PersonService().get_profile_completion(person=self)
        return super().save(*args, **kwargs)

    def get_first_name_display(self) -> str:
        if self.preferred_first_name:
            return self.preferred_first_name
        return self.first_name

    def get_workdays_display(self) -> str:
        workdays = self.workdays.all_mon_to_sun()

        workday_codes = [x.code for x in workdays]
        mon_to_fri_codes = ["mon", "tue", "wed", "thu", "fri"]

        # "Monday to Friday"
        if workday_codes == mon_to_fri_codes:
            return f"{workdays[0]} to {workdays[-1]}"

        # "Monday, Tuesday, Wednesday, ..."
        return ", ".join(map(str, workdays))

    def get_office_location_display(self) -> str:
        if self.international_building:
            return self.international_building

        location_parts = []

        if self.location_in_building:
            location_parts.append(escape(strip_tags(self.location_in_building)))

        if self.uk_office_location:
            if self.uk_office_location.building_name:
                location_parts.append(self.uk_office_location.building_name)
                location_parts.append(self.uk_office_location.city)
            else:
                for location_part in self.uk_office_location.name.split(","):
                    if clean_location_part := location_part.strip():
                        location_parts.append(clean_location_part)

        return mark_safe("<br>".join(location_parts))  # noqa: S308

    def get_manager_display(self) -> Optional[str]:
        if self.manager:
            return mark_safe(  # noqa: S308
                render_to_string(
                    "peoplefinder/components/profile-link.html",
                    {
                        "profile": self.manager,
                        "data_testid": "manager",
                    },
                )
            )
        return None

    def get_roles_display(self) -> Optional[str]:
        output = ""
        for role in self.roles.select_related("team").all():
            output += render_to_string(
                "peoplefinder/components/profile-role.html", {"role": role}
            )
        return mark_safe(output)  # noqa: S308

    def get_grade_display(self) -> Optional[str]:
        if self.grade:
            return self.grade.name
        return None

    def get_key_skills_display(self) -> Optional[str]:
        if self.key_skills.exists() or self.other_key_skills:
            skills_list = []
            skills_list += self.key_skills.values_list("name", flat=True)
            if self.other_key_skills:
                skills_list.append(self.other_key_skills)
            return ", ".join(skills_list)

        return None

    def get_learning_interests_display(self) -> Optional[str]:
        if self.learning_interests.exists() or self.other_learning_interests:
            interests_list = []
            interests_list += self.learning_interests.values_list("name", flat=True)
            if self.other_learning_interests:
                interests_list.append(self.other_learning_interests)
            return ", ".join(interests_list)

        return None

    def get_networks_display(self) -> Optional[str]:
        if self.networks.exists():
            return ", ".join(self.networks.values_list("name", flat=True))

        return None

    def get_professions_display(self) -> Optional[str]:
        if self.professions.exists():
            return ", ".join(self.professions.values_list("name", flat=True))

        return None

    def get_additional_roles_display(self) -> Optional[str]:
        if self.additional_roles.exists() or self.other_additional_roles:
            additional_roles_list = []
            additional_roles_list += self.additional_roles.values_list(
                "name", flat=True
            )
            if self.other_additional_roles:
                additional_roles_list.append(self.other_additional_roles)
            return ", ".join(additional_roles_list)

        return None


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

    indexed_fields = [
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

    search_fields = []

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
    def leader_count(self) -> int:
        return self.members.active().filter(head_of_team=True).count()

    @property
    def leaders(self):
        order_by = []

        if self.leaders_ordering == self.LeadersOrdering.CUSTOM:
            order_by.append("leaders_position")

        order_by += ["person__last_name", "person__first_name"]

        yield from (
            self.members.active()
            .select_related(
                "person",
                "person__uk_office_location",
            )
            .filter(head_of_team=True)
            .order_by(*order_by)
        )

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
