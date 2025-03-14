from django import template
from wagtail.models import Page, PageLogEntry


register = template.Library()


@register.simple_tag()
def get_published_rows(page: Page):
    return [
        [ple.timestamp, ple.user.profile]
        for ple in PageLogEntry.objects.filter(page=page)
        if ple.action == "wagtail.publish"
    ]
