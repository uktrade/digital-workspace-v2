from typing import Any, Dict, Union

from django import template
from django.urls import reverse
from django.utils.safestring import SafeString

from peoplefinder.models import Person
from peoplefinder.services.person import PersonService

register = template.Library()


@register.inclusion_tag("peoplefinder/partials/profile-completion-field-tag.html")
def profile_field_anchor(profile, *field_names) -> Union[SafeString, str]:
    core_field_ids = [
        f"core_field_id_{field_name}" for field_name in field_names if field_name
    ]

    context = {"core_field_ids": core_field_ids}
    return context


@register.inclusion_tag("peoplefinder/partials/profile-completion-field-link.html")
def profile_completion_field_actions(field_name, profile) -> Union[SafeString, str]:
    try:
        profile_field = Person._meta.get_field(field_name)
        human_readable_field_name = profile_field.verbose_name
    except Exception:
        human_readable_field_name = field_name.replace("_", " ")

    context: Dict[str, Any] = {
        "show_link": False,
        "human_readable_field_name": human_readable_field_name,
        "profile_edit_url": (
            reverse("profile-edit", args=[profile.slug])
            + f"#core_field_id_{field_name}"
        ),
    }

    field_statuses = PersonService().profile_completion_field_statuses(profile)
    if not field_statuses.get(field_name, False):
        context.update(show_link=True)
    return context
