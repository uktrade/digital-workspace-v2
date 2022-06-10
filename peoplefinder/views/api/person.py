from django.conf import settings
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
    class Meta:
        model = Person
        fields = [
            "people_finder_id",
            "staff_sso_id",
            "email",
            "contact_email",
            "full_name",
            "first_name",
            "last_name",
            "profile_url",
            "roles",
            "formatted_roles",
            "manager_people_finder_id",
            "completion_score",
            "is_stale",
            "works_monday",
            "works_tuesday",
            "works_wednesday",
            "works_thursday",
            "works_friday",
            "works_saturday",
            "works_sunday",
            "primary_phone_number",
            "secondary_phone_number",
            "formatted_location",
            "buildings",
            "formatted_buildings",
            "city",
            "country",
            "country_name",
            "grade",
            "formatted_grade",
            "location_in_building",
            "location_other_uk",
            "location_other_overseas",
            "key_skills",
            "other_key_skills",
            "formatted_key_skills",
            "learning_and_development",
            "other_learning_and_development",
            "formatted_learning_and_development",
            "networks",
            "formatted_networks",
            "professions",
            "formatted_professions",
            "additional_responsibilities",
            "other_additional_responsibilities",
            "formatted_additional_responsibilities",
            "language_fluent",
            "language_intermediate",
            "created_at",
            "last_edited_or_confirmed_at",
            "login_count",
            "last_login_at",
            # New fields
            "slug",
            "manager_slug",
            "legacy_people_finder_slug",
        ]

    people_finder_id = serializers.IntegerField(source="pk")
    staff_sso_id = serializers.CharField(source="user.legacy_sso_user_id", default=None)
    profile_url = serializers.SerializerMethodField()
    roles = TeamMemberSerialiser(many=True, read_only=True)
    formatted_roles = serializers.ListField(child=serializers.CharField())
    manager_people_finder_id = serializers.IntegerField(source="manager_id")
    completion_score = serializers.IntegerField(source="profile_completion")
    works_monday = serializers.SerializerMethodField()
    works_tuesday = serializers.SerializerMethodField()
    works_wednesday = serializers.SerializerMethodField()
    works_thursday = serializers.SerializerMethodField()
    works_friday = serializers.SerializerMethodField()
    works_saturday = serializers.SerializerMethodField()
    works_sunday = serializers.SerializerMethodField()
    formatted_location = serializers.SerializerMethodField()
    buildings = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )
    formatted_buildings = serializers.CharField()
    city = serializers.CharField(source="town_city_or_region")
    country = serializers.SlugRelatedField(read_only=True, slug_field="iso_2_code")
    country_name = serializers.StringRelatedField(read_only=True, source="country")
    grade = serializers.SlugRelatedField(read_only=True, slug_field="code")
    formatted_grade = serializers.StringRelatedField(read_only=True, source="grade")
    location_other_uk = serializers.CharField(source="regional_building")
    location_other_overseas = serializers.CharField(source="international_building")
    key_skills = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )
    formatted_key_skills = serializers.CharField()
    learning_and_development = serializers.SlugRelatedField(
        many=True, read_only=True, source="learning_interests", slug_field="code"
    )
    other_learning_and_development = serializers.CharField(
        source="other_learning_interests"
    )
    formatted_learning_and_development = serializers.CharField()
    networks = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )
    formatted_networks = serializers.CharField()
    professions = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )
    formatted_professions = serializers.CharField()
    additional_responsibilities = serializers.SlugRelatedField(
        many=True, read_only=True, source="additional_roles", slug_field="code"
    )
    other_additional_responsibilities = serializers.CharField(
        source="other_additional_roles"
    )
    formatted_additional_responsibilities = serializers.CharField()
    language_fluent = serializers.CharField(source="fluent_languages")
    language_intermediate = serializers.CharField(source="intermediate_languages")
    last_edited_or_confirmed_at = serializers.DateTimeField(
        source="edited_or_confirmed_at"
    )
    last_login_at = serializers.SerializerMethodField()
    # New fields
    slug = serializers.CharField()
    manager_slug = serializers.SlugRelatedField(
        read_only=True, source="manager", slug_field="slug"
    )
    legacy_people_finder_slug = serializers.CharField(source="legacy_slug")

    def get_last_login_at(self, obj):
        return obj.user and obj.user.last_login

    def _workday(self, obj, code):
        if obj.workday_list:
            return code in obj.workday_list

        return False

    def get_works_monday(self, obj):
        return self._workday(obj, "mon")

    def get_works_tuesday(self, obj):
        return self._workday(obj, "tue")

    def get_works_wednesday(self, obj):
        return self._workday(obj, "wed")

    def get_works_thursday(self, obj):
        return self._workday(obj, "thu")

    def get_works_friday(self, obj):
        return self._workday(obj, "fri")

    def get_works_saturday(self, obj):
        return self._workday(obj, "sat")

    def get_works_sunday(self, obj):
        return self._workday(obj, "sun")

    def get_formatted_location(self, obj):
        parts = (
            obj.location_in_building,
            *[x.name for x in obj.buildings.all()],
            obj.town_city_or_region,
        )

        if not any(parts):
            return None

        return ", ".join(filter(None, parts))

    def get_profile_url(self, obj):
        return settings.BASE_URL + obj.get_absolute_url()


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
    lookup_field = "legacy_sso_user_id"

    @decorator_from_middleware(HawkResponseMiddleware)
    def retrieve(self, request, legacy_sso_user_id=None):
        return super().retrieve(self, request, legacy_sso_user_id)

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        return super().list(self, request)

    def get_queryset(self):
        queryset = (
            Person.objects.get_annotated()
            .select_related("country", "grade", "user", "manager")
            .prefetch_related("roles", "roles__team")
            .with_profile_completion()
            .defer("photo", "do_not_work_for_dit")
            .order_by("-created_at")
        )

        return queryset
