import hashlib

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def profile_photo_attrs(profile) -> str:
    if not profile.roles.filter(team__name="Employee Experience").exists():
        return ""

    def byte_hash(val: str):
        return int(hashlib.sha256(val.encode("utf-8")).hexdigest(), 16) % 255

    attrs = {
        "class": "profile-photo",
        "style": (
            f"--color-1: {byte_hash(profile.first_name)};"
            f" --color-2: {byte_hash(profile.last_name)};"
            f" --color-3: {byte_hash(profile.get_first_name_display())};"
        ),
    }
    return mark_safe(" ".join([f'{k}="{v}"' for k, v in attrs.items()]))  # noqa S308
