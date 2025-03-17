from django import template
from django.conf import settings
from wagtail.models import Page
from peoplefinder.models import Person
from django.urls import reverse
from django.utils import timezone

register = template.Library()


@register.inclusion_tag("dwds/components/author.html")
def page_author(page: Page):
    person = page.owner.profile
    return {
        "name": person.full_name,
        "profile_image_url": (
            person.photo.url
            if person.photo
            else None
        ),
        "profile_url": reverse('profile-view', args=[person.slug]),
        "published_timestamp": timezone.now(),
        "updated_timestamp": timezone.now(),
    }
