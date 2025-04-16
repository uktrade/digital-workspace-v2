from django.core.exceptions import ValidationError
from wagtail.models import Page


def validate_home_priority_pages(value):
    from home.models import HOME_PRIORITY_PAGE_TYPES

    p = Page.objects.get(id=value).specific
    if not issubclass(p.__class__, HOME_PRIORITY_PAGE_TYPES):
        raise ValidationError(
            "Only NewsPage objects can be added to the priority pages list",
        )
