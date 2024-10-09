from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from dev_tools.forms import ChangeUserForm


User = get_user_model()


def check_dev_tools_enabled(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEV_TOOLS_ENABLED:
            raise SuspiciousOperation("Dev tools are not enabled")

        return func(*args, **kwargs)

    return wrapper


@require_http_methods(["GET"])
@check_dev_tools_enabled
def login_view(request):
    assert settings.DEV_TOOLS_DEFAULT_USER

    user = User.objects.get(pk=settings.DEV_TOOLS_DEFAULT_USER)
    login(request, user)
    messages.success(request, f"Automatically logged in as {user}")

    return redirect(settings.LOGIN_REDIRECT_URL)


@require_http_methods(["POST"])
@check_dev_tools_enabled
def change_user_view(request):
    next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)

    form = ChangeUserForm(data=request.POST)

    if not form.is_valid():
        raise ValidationError("Invalid change user form")

    if form.cleaned_data["user"]:
        new_user = User.objects.get(pk=form.cleaned_data["user"])

        login(request, new_user)
        messages.success(request, f"Logged in as {new_user}")
    else:
        logout(request)
        messages.success(request, "Logged out")

    if is_valid_redirect_url(next_url):
        return redirect(next_url)
    redirect(settings.LOGIN_REDIRECT_URL)


def is_valid_redirect_url(url: str) -> bool:
    if url[0] != "/" and "trade.gov.uk" not in url:
        return False
    return True
