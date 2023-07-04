from typing import Union

from django import template
from django.urls import reverse
from django.utils.safestring import SafeString, mark_safe

from peoplefinder.utils import profile_completion_field_statuses

register = template.Library()


@register.simple_tag
def profile_completion_field_tag(field_name, profile) -> Union[SafeString, str]:
    core_field_id = f"core_field_id_{field_name}"
    tag = mark_safe(
        f'<strong id="{core_field_id}" class="govuk-tag">Recommended</strong>'
    )
    field_statuses = profile_completion_field_statuses(profile)
    if field_name in field_statuses and not field_statuses[field_name]:
        return tag
    return ""


@register.simple_tag
def profile_completion_field_link(field_name, profile) -> Union[SafeString, str]:
    human_readable_field_name = field_name.replace("_", " ")
    profile_edit_url = reverse("profile-edit", args=[profile.slug])
    edit_field_link = mark_safe(
        f'<a class="govuk-link" href="{profile_edit_url}#core_field_id_{field_name}">Add {human_readable_field_name}</a>'
    )
    field_statuses = profile_completion_field_statuses(profile)
    if field_name in field_statuses and not field_statuses[field_name]:
        return edit_field_link
    return ""
