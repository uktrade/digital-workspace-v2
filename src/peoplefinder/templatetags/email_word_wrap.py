from django import template


register = template.Library()


@register.filter
def email_word_wrap(email: str) -> str:
    print(f"Filter called with: {email}")
    if not isinstance(email, str):
        return email

    email = email.replace("@", "<wbr>@")
    email = email.replace(".gov.uk", "<wbr>.gov.uk")

    return email
