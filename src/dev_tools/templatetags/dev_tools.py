from django import template
from django.conf import settings
from django.template.loader import render_to_string

from dev_tools.forms import ChangeUserForm


register = template.Library()


@register.simple_tag(takes_context=True)
def dev_tools_dialog(context):
    if not hasattr(settings, "DEV_TOOLS_ENABLED") or not (
        settings.DEBUG and settings.DEV_TOOLS_ENABLED
    ):
        return ""

    request = context["request"]

    context = {
        "change_user_form": ChangeUserForm(initial={"user": request.user.pk}),
    }

    return render_to_string("dev_tools/dialog.html", context=context, request=request)
