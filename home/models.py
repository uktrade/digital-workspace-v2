import atoma
import requests
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import (
    FieldPanel,
    PageChooserPanel,
)
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet

from content.models import BasePage
from home.util import get_tweets
from news.models import NewsPage
from working_at_dit.models import HowDoI


@register_snippet
class QuickLink(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        "content.ContentPage",
        on_delete=models.CASCADE,
        related_name="quick_links_pages",
    )

    def __str__(self):
        return f"'{self.title}' which links to the '{self.link_to.title}' page"

    panels = [
        FieldPanel("title"),
        PageChooserPanel("link_to"),
    ]

    class Meta:
        ordering = ["-title"]


@register_snippet
class WhatsPopular(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        "content.ContentPage",
        on_delete=models.CASCADE,
        related_name="whats_popular_pages",
        blank=True,
        null=True,
    )
    external_url = models.URLField(
        blank=True,
        null=True,
    )
    preview_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("title"),
        ImageChooserPanel("preview_image"),
        PageChooserPanel("link_to"),
        FieldPanel("external_url"),
    ]

    class Meta:
        ordering = ["-title"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.external_url and self.link_to:
            raise ValidationError(
                "Please choose an external URL or a page within the site. "
                "You cannot have both."
            )

        if (
            WhatsPopular.objects.count() == 3
            and self.id  # noqa W504
            not in WhatsPopular.objects.all().values_list("id", flat=True)
        ):
            raise ValidationError(
                'You can have a maximum of 3 "what\'s popular" pages. '
                "Please remove one of the others before adding a new one."
            )


class HomePage(BasePage):
    is_creatable = False
    show_in_menus = True

    subpage_types = []

    promote_panels = []

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)

        # Quick links
        quick_links = QuickLink.objects.all()
        context["quick_links"] = quick_links

        # News
        news_items = (
            NewsPage.objects.live()
            .public()
            .order_by(
                "-pinned_on_home",
                "result_weighting",
                "-last_published_at",
            )[:8]
        )
        context["news_items"] = news_items

        #  Tweets
        if not cache.get("homepage_tweets"):
            cache.set(
                "homepage_tweets",
                sorted(get_tweets(), key=lambda x: x.created_at, reverse=True),
                3000,
            )

        context["tweets"] = cache.get("homepage_tweets")[:3]

        # What's popular
        context["whats_popular_items"] = WhatsPopular.objects.all()

        # How do I
        context["how_do_i_items"] = (
            HowDoI.objects.filter(include_link_on_homepage=True)
            .live()
            .public()
            .order_by(
                "title",
            )[:10]
        )

        # GOVUK news
        if not cache.get("homepage_govuk_news"):
            govuk_news_feed_url = "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=department-for-international-trade"

            response = requests.get(govuk_news_feed_url)
            feed = atoma.parse_atom_bytes(response.content)

            cache.set(
                "homepage_govuk_news",
                feed.entries[:6],
                3000,
            )

        context["govuk_feed"] = cache.get("homepage_govuk_news")

        return context
