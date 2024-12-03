from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()



# Split on @ -> name_part + domain_part

# Name: split on .-_ -> name_parts ["name", "middle", "-name" ".surname"]
# Domain: split on .-_ -> domain_parts ["example", ".com"]

# For each name_part in name_parts: Split if longer than X
# For each domain_part in name_parts: Split if longer than X

# Add all parts back together with <wbr> being the glue


@register.filter
def email_word_break(email: str) -> str:
    if not email or not isinstance(email, str):
        # raise typerror/valueerror, check python
        return email

    email = escape(email)
    if "." in email:
        name_parts = email.split(".", 1)
        email = f"{name_parts[0]}<wbr>.{name_parts[1]}"
    email = email.replace("@", "<wbr>@")
    email = email.replace(".gov.uk", "<wbr>.gov.uk")

    return mark_safe(email)  # noqa S308
