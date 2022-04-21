from django.db import models
from wagtail.admin.edit_handlers import FieldPanel

from content.models import ContentPage


class NetworksHome(ContentPage):
    is_creatable = False

    subpage_types = ["networks.Network"]


class Network(ContentPage):
    excerpt = models.CharField(
        max_length=700,
        blank=True,
        null=True,
    )

    is_creatable = True

    parent_page_types = [
        "networks.NetworksHome",
        "networks.Network",
    ]
    subpage_types = ["networks.Network"]

    content_panels = ContentPage.content_panels + [FieldPanel("excerpt")]
