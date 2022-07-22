from django.utils.decorators import decorator_from_middleware, method_decorator
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication
from rest_framework import serializers
from rest_framework.viewsets import ReadOnlyModelViewSet

from peoplefinder.models import Team

from .base import ApiPagination


class TeamSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(source="id")
    team_name = serializers.CharField(source="name")
    parent_id = serializers.SerializerMethodField()
    ancestry = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["team_id", "team_name", "parent_id", "ancestry"]

    def get_parent_id(self, obj):
        parents = obj.ancestry[:-1]

        return parents[-1] if parents else None

    def get_ancestry(self, obj):
        return "/".join(map(str, obj.ancestry[:-1]))


class TeamPagination(ApiPagination):
    ordering = "pk"


@method_decorator(decorator_from_middleware(HawkResponseMiddleware), name="list")
@method_decorator(decorator_from_middleware(HawkResponseMiddleware), name="retrieve")
class TeamView(ReadOnlyModelViewSet):
    authentication_classes = [HawkAuthentication]
    permission_classes = []
    serializer_class = TeamSerializer
    pagination_class = TeamPagination

    def get_queryset(self):
        return Team.objects.with_parents()
