from typing import Any, Dict, Union

from django import template
from django.urls import reverse
from django.utils.safestring import SafeString

from peoplefinder.utils import profile_completion_field_statuses

register = template.Library()


@register.inclusion_tag("peoplefinder/partials/profile-completion-field-tag.html")
def profile_field_anchor(profile, *field_names) -> Union[SafeString, str]:
    core_field_ids = [
        f"core_field_id_{field_name}" for field_name in field_names if field_name
    ]

    context = {"core_field_ids": core_field_ids}
    return context


@register.inclusion_tag("peoplefinder/partials/profile-completion-field-link.html")
def profile_completion_field_link(field_name, profile) -> Union[SafeString, str]:
    context: Dict[str, Any] = {
        "show_link": False,
        "human_readable_field_name": field_name.replace("_", " "),
        "profile_edit_url": (
            reverse("profile-edit", args=[profile.slug])
            + f"#core_field_id_{field_name}"
        ),
    }

    field_statuses = profile_completion_field_statuses(profile)
    if field_name in field_statuses and not field_statuses[field_name]:
        context.update(show_link=True)
    return context
