from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import PageChooserPanel
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet

from core.panels import FieldPanel, InlinePanel


@register_snippet
class Nav(ClusterableModel):
    panels = [
        InlinePanel("links", label="Links"),
    ]


class NavLinkBase(Orderable):
    label = models.CharField(max_length=255)
    url = models.URLField(null=True, blank=True)
    page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )

    def get_url(self):
        if self.page:
            return self.page.get_full_url()
        return self.url

    def __str__(self):
        return self.label

    panels = [
        FieldPanel("label"),
        FieldPanel("url"),
        PageChooserPanel("page"),
    ]

    class Meta(Orderable.Meta):
        abstract = True


class PrimaryNavLink(NavLinkBase, ClusterableModel):
    navigation = ParentalKey(
        "Nav",
        on_delete=models.PROTECT,
        related_name="links",
    )

    panels = NavLinkBase.panels + [
        InlinePanel("child_links", label="Sub links"),
    ]


class SecondaryNavLink(NavLinkBase):
    parent_link = ParentalKey(
        "PrimaryNavLink",
        on_delete=models.PROTECT,
        null=True,
        related_name="child_links",
    )
