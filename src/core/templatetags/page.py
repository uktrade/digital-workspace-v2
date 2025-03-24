import urllib.parse

from django import template
from django.http import HttpRequest
from django.urls import reverse
from wagtail.models import Page


register = template.Library()


@register.inclusion_tag("dwds/components/author.html")
def page_author(page: Page):
    person = page.owner.profile
    return {
        "name": person.full_name,
        "profile_image_url": (person.photo.url if person.photo else None),
        "profile_url": reverse("profile-view", args=[person.slug]),
        "published_timestamp": page.first_published_at,
        "updated_timestamp": page.last_published_at,
    }


@register.simple_tag
def get_share_page_email_link(request: HttpRequest, page: Page) -> str:
    to_email = ""
    params: dict[str, str] = {
        "cc": "",
        "bcc": "",
        "subject": f"{page.title} - DBT Intranet",
        "body": (
            page.get_full_url(request)
            + urllib.parse.quote_plus("\n")
            + "Only people with access to the Department for Business and Trade"
            " intranet can open this link."
        ),
    }
    params_str = "&".join([f"{key}={value}" for key, value in params.items() if value])
    return f"mailto:{to_email}?{params_str}"
