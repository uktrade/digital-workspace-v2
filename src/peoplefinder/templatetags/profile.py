import hashlib

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def print_attrs(attrs: dict) -> str:
    return mark_safe(" ".join([f'{k}="{v}"' for k, v in attrs.items()]))  # noqa S308


@register.simple_tag
def profile_photo_attrs(profile) -> str:
    attrs = {
        "class": "",
    }
    if not profile.roles.filter(team__name="Employee Experience").exists():
        return print_attrs(attrs)

    def byte_hash(val: str):
        return int(hashlib.sha256(val.encode("utf-8")).hexdigest(), 16) % 255

    attrs["class"] += " profile-photo"
    attrs["style"] = (
        f"--color-1: {byte_hash(profile.first_name)};"
        f" --color-2: {byte_hash(profile.last_name)};"
        f" --color-3: {byte_hash(profile.get_first_name_display())};"
    )
    return print_attrs(attrs)
