from django.conf import settings
from django.utils.decorators import decorator_from_middleware
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication
from rest_framework import serializers
from rest_framework.viewsets import ReadOnlyModelViewSet

from peoplefinder.models import Person, TeamMember

from .base import ApiPagination


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


class PersonPkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["pk"]


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
            "city",
            "country",
            "country_name",
            "grade",
            "formatted_grade",
            "uk_office_location",
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
            "legacy_sso_user_id",
            "sso_user_id",
            "slug",
            "manager_slug",
            "legacy_people_finder_slug",
            "photo",
            "photo_small",
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
    city = serializers.SerializerMethodField()
    country = serializers.SlugRelatedField(read_only=True, slug_field="iso_2_code")
    country_name = serializers.StringRelatedField(read_only=True, source="country")
    grade = serializers.SlugRelatedField(read_only=True, slug_field="code")
    formatted_grade = serializers.StringRelatedField(read_only=True, source="grade")
    location_other_uk = serializers.CharField(source="regional_building")
    location_other_overseas = serializers.CharField(source="international_building")
    uk_office_location = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
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
    sso_user_id = serializers.CharField(source="user.username", default=None)
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

    def get_city(self, obj):
        if obj.uk_office_location:
            return obj.uk_office_location.city
        return obj.town_city_or_region

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
        return settings.WAGTAILADMIN_BASE_URL + obj.get_absolute_url()


# WARNING: We need PersonPagination and PersonViewSet.get_full_queryset to have the same
# ordering for the performance optimisations to work.
PERSON_ORDERING = "-pk"


class PersonPagination(ApiPagination):
    ordering = PERSON_ORDERING


class PersonViewSet(ReadOnlyModelViewSet):
    authentication_classes = (HawkAuthentication,)
    permission_classes = ()
    pagination_class = PersonPagination
    serializer_class = PersonPkSerializer
    queryset = Person.active.only("pk").all()
    lookup_field = "legacy_sso_user_id"

    @decorator_from_middleware(HawkResponseMiddleware)
    def retrieve(self, request, legacy_sso_user_id=None):
        return super().retrieve(self, request, legacy_sso_user_id)

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        # The following code is here to optimise the large and complex queries that are
        # behind this API endpoint.

        # The combination of many joins and a limit clause applied by the pagination had
        # very slow performance. To fix this, we will perform a slim query to get the
        # rows that are in the page, and then use the PKs from those rows as a filter to
        # the full query. This avoids the need for a limit clause on the full query and
        # speed up the query significantly. Some local testing indicates that the
        # performance increase is 10x.

        # this first call to list will use the slim queryset and serializer
        response = super().list(self, request)

        # we use that response to get a list of all the PKs in the paged results
        pks = [x["pk"] for x in response.data.get("results", [])]

        # then pass those PKs to the full queryset and serializer
        serializer = PersonSerializer(self.get_full_queryset(pks), many=True)

        # then replace the results with the full data
        response.data["results"] = serializer.data

        # and finally return the modified response
        return response

    def get_full_queryset(self, pks):
        return (
            Person.active.get_annotated()
            .select_related("country", "grade", "user", "manager")
            .prefetch_related(
                "roles__team",
                "key_skills",
                "workdays",
                "learning_interests",
                "networks",
                "professions",
                "additional_roles",
                "buildings",
            )
            .defer("do_not_work_for_dit")
            .filter(pk__in=pks)
            .order_by(PERSON_ORDERING)
        )
