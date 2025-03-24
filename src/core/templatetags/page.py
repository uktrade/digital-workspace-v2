from django import template
from django.conf import settings
from django.urls import reverse
from wagtail.models import Page

from peoplefinder.models import Person


register = template.Library()


@register.inclusion_tag("dwds/components/author.html")
def page_author(page: Page):
    person = page.owner.profile

    if page_author := getattr(page, "page_author", False):
        person = page_author
    elif getattr(page, "perm_sec_as_author", False) and settings.PERM_SEC_NAME:
        perm_sec_names = settings.PERM_SEC_NAME.split(" ")
        person = Person.objects.get(
            first_name=perm_sec_names[0], last_name=perm_sec_names[1]
        )

    return {
        "name": person.full_name,
        "profile_image_url": (person.photo.url if person.photo else None),
        "profile_url": reverse("profile-view", args=[person.slug]),
        "published_timestamp": page.first_published_at,
        "updated_timestamp": page.last_published_at,
    }
