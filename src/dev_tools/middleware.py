from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


EXCLUDED_APP_NAMES = ("admin", "dev_tools")


class DevToolsLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        assert settings.DEV_TOOLS_ENABLED

    def __call__(self, request):
        assert hasattr(request, "user")

        if (
            not request.user.is_authenticated
            and resolve(request.path).app_name not in EXCLUDED_APP_NAMES
        ):
            return redirect(self.get_login_url())

        response = self.get_response(request)

        return response

    def get_login_url(self):
        return settings.DEV_TOOLS_LOGIN_URL or settings.LOGIN_URL
