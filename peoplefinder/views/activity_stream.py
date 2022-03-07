from django.http import JsonResponse
from django.utils.decorators import decorator_from_middleware

from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication

from rest_framework.viewsets import ViewSet


class ActivityStreamViewSet(ViewSet):
    authentication_classes = (HawkAuthentication,)
    permission_classes = ()

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        return JsonResponse(
            {
                "test_data": 1,
            },
        )
