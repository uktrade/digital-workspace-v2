from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg, StringAgg
from django.utils.decorators import decorator_from_middleware
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication
from rest_framework import pagination, serializers
from rest_framework.viewsets import ReadOnlyModelViewSet

from peoplefinder.models import Person, TeamMember


class TeamMemberSerialiser(serializers.ModelSerializer):
    role = serializers.CharField(source="job_title")
    team_name = serializers.CharField(source="team.name")
    team_id = serializers.IntegerField()
    leader = serializers.BooleanField(source="head_of_team")

    class Meta:
        model = TeamMember
        fields = [
            "role",
            "team_name",
            "team_id",
            "leader",
        ]


class PersonSerializer(serializers.ModelSerializer):
    buildings = serializers.CharField(source="building_codes")
    works_monday = serializers.SerializerMethodField()
    works_tuesday = serializers.SerializerMethodField()
    works_wednesday = serializers.SerializerMethodField()
    works_thursday = serializers.SerializerMethodField()
    works_friday = serializers.SerializerMethodField()
    works_saturday = serializers.SerializerMethodField()
    works_sunday = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    formatted_grade = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    formatted_location = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()
    networks = serializers.CharField(source="network_codes")
    formatted_networks = serializers.CharField()
    additional_responsibilities = serializers.CharField()
    formatted_additional_responsibilities = serializers.CharField()
    key_skills = serializers.CharField(source="key_skill_codes")
    learning_and_development = serializers.CharField()
    formatted_learning_and_development = serializers.CharField()
    professions = serializers.CharField(source="profession_codes")
    formatted_professions = serializers.CharField()
    completion_score = serializers.IntegerField(source="profile_completion")
    city = serializers.CharField(source="town_city_or_region")
    language_fluent = serializers.CharField(source="fluent_languages")
    language_intermediate = serializers.CharField(source="intermediate_languages")
    last_edited_or_confirmed_at = serializers.DateTimeField(source="updated_at")
    people_finder_id = serializers.CharField(source="slug")
    staff_sso_id = serializers.CharField(source="user.legacy_sso_user_id", default=None)
    location_other_uk = serializers.CharField(source="regional_building")
    location_other_overseas = serializers.CharField(source="international_building")
    formatted_buildings = serializers.CharField()
    formatted_key_skills = serializers.CharField()
    other_additional_responsibilities = serializers.CharField(
        source="other_additional_roles"
    )
    manager_people_finder_id = serializers.CharField(source="manager_id")
    roles = TeamMemberSerialiser(many=True, read_only=True)
    last_login_at = serializers.SerializerMethodField()
    formatted_roles = serializers.CharField()
    legacy_people_finder_id = serializers.CharField(source="legacy_slug")

    def get_last_login_at(self, obj):
        return obj.user and obj.user.last_login

    def get_grade(self, obj):
        if obj.grade:
            return obj.grade.code
        return ""

    def get_formatted_grade(self, obj):
        if obj.grade:
            return obj.grade.name
        return ""

    def get_country(self, obj):
        if obj.country:
            return obj.country.code
        else:
            return ""

    def get_country_name(self, obj):
        if obj.country:
            return obj.country.name
        else:
            return ""

    def workday(self, obj, code):
        if obj.workday_list:
            return code in obj.workday_list
        return False

    def get_works_monday(self, obj):
        return self.workday(obj, "mon")

    def get_works_tuesday(self, obj):
        return self.workday(obj, "tue")

    def get_works_wednesday(self, obj):
        return self.workday(obj, "wed")

    def get_works_thursday(self, obj):
        return self.workday(obj, "thu")

    def get_works_friday(self, obj):
        return self.workday(obj, "fri")

    def get_works_saturday(self, obj):
        return self.workday(obj, "sat")

    def get_works_sunday(self, obj):
        return self.workday(obj, "sun")

    class Meta:
        model = Person
        fields = [
            "email",
            "contact_email",
            "works_monday",
            "works_tuesday",
            "works_wednesday",
            "works_thursday",
            "works_friday",
            "works_saturday",
            "works_sunday",
            "location_in_building",
            "city",
            "country",
            "language_fluent",
            "language_intermediate",
            "grade",
            "created_at",
            "last_edited_or_confirmed_at",
            "login_count",
            "last_login_at",
            "people_finder_id",
            "legacy_people_finder_id",
            "staff_sso_id",
            "full_name",
            "first_name",
            "last_name",
            "primary_phone_number",
            "secondary_phone_number",
            "formatted_location",
            "location_other_uk",
            "location_other_overseas",
            "buildings",
            "formatted_buildings",
            "roles",
            "formatted_roles",
            "key_skills",
            "other_key_skills",
            "formatted_key_skills",
            "learning_and_development",
            "other_learning_interests",
            "formatted_learning_and_development",
            "networks",
            "formatted_networks",
            "professions",
            "formatted_professions",
            "additional_responsibilities",
            "other_additional_responsibilities",
            "formatted_additional_responsibilities",
            "manager_people_finder_id",
            "completion_score",
            "profile_url",
            "country_name",
            "formatted_grade",
            "is_stale",
        ]

    def get_formatted_location(self, obj):
        return f"{obj.location_in_building},  {obj.town_city_or_region}"

    def get_profile_url(self, obj):
        return obj.get_absolute_url()


class PersonPagination(pagination.CursorPagination):
    page_size = settings.PAGINATION_PAGE_SIZE
    max_page_size = settings.PAGINATION_MAX_PAGE_SIZE
    page_size_query_param = "page_size"
    ordering = "-created_at"


class PersonViewSet(ReadOnlyModelViewSet):
    authentication_classes = (HawkAuthentication,)
    permission_classes = ()
    serializer_class = PersonSerializer
    pagination_class = PersonPagination

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        return super().list(self, request)

    def get_queryset(self):
        queryset = (
            Person.objects.all()
            .prefetch_related("roles")
            .prefetch_related("roles__team")
            .select_related("country", "grade", "user", "manager")
            .annotate(
                formatted_roles=ArrayAgg(
                    "roles__team__name",
                    distinct=True,
                )
            )
            .annotate(
                network_codes=ArrayAgg(
                    "networks__code",
                    distinct=True,
                )
            )
            .annotate(
                formatted_networks=StringAgg(
                    "networks__name",
                    delimiter=", ",
                    distinct=True,
                )
            )
            .annotate(
                formatted_buildings=StringAgg(
                    "buildings__name",
                    delimiter=", ",
                    distinct=True,
                )
            )
            .annotate(
                building_codes=ArrayAgg(
                    "buildings__code",
                    distinct=True,
                )
            )
            .annotate(
                additional_responsibilities=ArrayAgg(
                    "additional_roles__code",
                    distinct=True,
                )
            )
            .annotate(
                formatted_additional_responsibilities=StringAgg(
                    "additional_roles__name",
                    delimiter="' ",
                    distinct=True,
                )
            )
            .annotate(
                key_skill_codes=ArrayAgg(
                    "key_skills__code",
                    distinct=True,
                )
            )
            .annotate(
                formatted_key_skills=StringAgg(
                    "key_skills__name",
                    delimiter=", ",
                    distinct=True,
                )
            )
            .annotate(
                learning_and_development=ArrayAgg(
                    "learning_interests__name",
                    distinct=True,
                )
            )
            .annotate(
                formatted_learning_and_development=StringAgg(
                    "learning_interests__code",
                    delimiter=", ",
                    distinct=True,
                )
            )
            .annotate(
                profession_codes=ArrayAgg(
                    "professions__code",
                    distinct=True,
                )
            )
            .annotate(
                formatted_professions=StringAgg(
                    "professions__name",
                    delimiter="' ",
                    distinct=True,
                )
            )
            .annotate(
                workday_list=ArrayAgg(
                    "workdays__code",
                    distinct=True,
                )
            )
            .with_profile_completion()
            .defer("photo", "do_not_work_for_dit")
            .order_by("-created_at")
        )
        return queryset
