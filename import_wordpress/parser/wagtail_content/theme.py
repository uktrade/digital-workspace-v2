from django.template.defaultfilters import slugify

from content.models import Theme


def create_theme(theme):
    Theme.objects.get_or_create(
        title=theme["title"], slug=slugify(theme["title"]), summary=theme["excerpt"]
    )
