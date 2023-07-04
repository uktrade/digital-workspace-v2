from typing import Union

from django import template
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
