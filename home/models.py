from django.db import models
from django.core.exceptions import ValidationError
import atoma
import requests
from home.util import get_tweets
from django.core.cache import cache

from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.admin.edit_handlers import (
    FieldPanel,
    PageChooserPanel,
)
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey
from wagtail.core.models import Page

from news.models import NewsPage

from working_at_dit.models import HowDoI


@register_snippet
class QuickLink(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        'content.ContentPage',
        on_delete=models.CASCADE,
        related_name='quick_links_pages',
    )

    def __str__(self):
        return f"'{self.title}' which links to the '{self.link_to.title}' page"

    panels = [
        FieldPanel('title'),
        PageChooserPanel('link_to'),
    ]

    class Meta:
        ordering = ['-title']


@register_snippet
class WhatsPopular(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        'content.ContentPage',
        on_delete=models.CASCADE,
        related_name='whats_popular_pages',
        blank=True,
        null=True,
    )
    external_url = models.URLField(
        blank=True,
        null=True,
    )
    preview_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('title'),
        ImageChooserPanel("preview_image"),
        PageChooserPanel('link_to'),
        FieldPanel('external_url'),
    ]

    class Meta:
        ordering = ['-title']

    def __str__(self):
        return self.title

    def clean(self):
        if self.external_url and self.link_to:
            raise ValidationError(
                "Please choose an external URL or a page within the site. "
                "You cannot have both."
            )

        if WhatsPopular.objects.count() == 3 and self.id not in WhatsPopular.objects.all().values_list('id', flat=True):
            raise ValidationError(
                "You can have a maximum of 3 \"what's popular\" pages. "
                "Please remove one of the others before adding a new one."
            )


@register_snippet
class HowDoIPreview(models.Model):
    how_do_i_page = ParentalKey(
        'working_at_dit.HowDoI',
        on_delete=models.CASCADE,
        related_name='how_do_i_on_home_pages',
    )

    def __str__(self):
        return self.how_do_i_page

    panels = [
        PageChooserPanel('how_do_i_page'),
    ]


class HomePage(Page):
    is_creatable = False
    show_in_menus = True

    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)

        # Quick links
        quick_links = QuickLink.objects.all()
        context['quick_links'] = quick_links

        # News
        news_items = NewsPage.objects.live().public().order_by(
            '-first_published_at',
        )[:8]
        context['news_items'] = news_items

        # Tweets
        if not cache.get('homepage_tweets'):
            cache.set(
                'homepage_tweets',
                sorted(get_tweets(), key=lambda x: x.created_at, reverse=True),
                3000,
            )

        context['tweets'] = cache.get('homepage_tweets')

        # What's popular
        context['whats_popular_items'] = WhatsPopular.objects.all()

        # How do I
        context['how_do_i_items'] = HowDoI.objects.live().public().order_by(
            '-first_published_at',
        )[:10]

        # GOVUK news
        govuk_news_feed_url = "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=department-for-international-trade"

        response = requests.get(govuk_news_feed_url)
        feed = atoma.parse_atom_bytes(response.content)

        context['govuk_feed'] = feed.entries[:6]

        return context
