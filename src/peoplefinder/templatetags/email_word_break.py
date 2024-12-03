from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def email_word_break(email: str) -> str:
    if not email or not isinstance(email, str):
        return email

    email = escape(email)
    if "." in email:
        name_parts = email.split(".", 1)
        email = f"{name_parts[0]}<wbr>.{name_parts[1]}"
    email = email.replace("@", "<wbr>@")
    email = email.replace(".gov.uk", "<wbr>.gov.uk")

    return mark_safe(email)  # noqa S308
