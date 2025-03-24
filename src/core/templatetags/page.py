from django import template
from django.urls import reverse
from wagtail.models import Page


register = template.Library()


@register.inclusion_tag("dwds/components/author.html")
def page_author(page: Page):
    page = page.specific

    context = {
        "name": "",
        "profile_image_url": None,
        "profile_url": None,
        "published_timestamp": page.first_published_at,
        "updated_timestamp": page.last_published_at,
    }

    author = page.get_author()

    if isinstance(author, str):
        context["name"] = author
        return context

    context.update(
        name=author.full_name,
        profile_image_url=(author.photo.url if author.photo else None),
    )
    if author.is_active:
        context.update(
            profile_url=reverse("profile-view", args=[author.slug]),
        )

    return context
