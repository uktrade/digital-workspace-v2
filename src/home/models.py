import re
from collections.abc import Iterator

import atoma
import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    MultiFieldPanel,
)
from wagtail.models import PagePermissionTester
from wagtail.snippets.models import register_snippet
from wagtail_adminsortable.models import AdminSortable
from wagtailorderable.models import Orderable

from content.models import BasePage, ContentPage
from core.models import fields
from core.panels import FieldPanel, InlinePanel, PageSelectorPanel
from events.models import EventPage
from home.forms import HomePageForm
from home.validators import validate_home_priority_pages
from news.models import NewsPage


HOME_PRIORITY_PAGE_TYPES = (
    NewsPage,
    EventPage,
)


@register_snippet
class HomeNewsOrder(AdminSortable, ClusterableModel):
    """
    This model has been deprecated and can be removed once we are happy with the
    new Home Page approach.
    """

    order = models.IntegerField(null=True, blank=True)
    news_page = ParentalKey(
        "news.NewsPage",
        on_delete=models.CASCADE,
        related_name="home_news_order_pages",
    )

    def __str__(self):
        return str(self.news_page)

    class Meta(AdminSortable.Meta):
        ordering = ["order"]
        verbose_name = "Home page news order"
        verbose_name_plural = "Home page news order"

    panels = [
        FieldPanel("news_page"),
    ]

    def clean(self):
        if not self.id:
            existing_news_page = HomeNewsOrder.objects.filter(
                news_page=self.news_page,
            ).first()

            if existing_news_page:
                raise ValidationError(
                    "This news page is already in the list",
                )


class HomePriorityPage(Orderable):
    home_page = ParentalKey(
        "home.HomePage",
        on_delete=models.CASCADE,
        related_name="priority_pages",
    )
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="priority_page",
        validators=[validate_home_priority_pages],
    )

    ribbon_text = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Insert a ribbon text for the news listing on the home page.",
    )

    panels = [
        PageSelectorPanel("page", HOME_PRIORITY_PAGE_TYPES),
        FieldPanel("ribbon_text"),
    ]

    class Meta:
        unique_together = ("home_page", "page")
        ordering = ["sort_order"]


@register_snippet
class QuickLink(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        "content.ContentPage",
        on_delete=models.CASCADE,
        related_name="quick_links_pages",
    )
    result_weighting = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"'{self.title}' which links to the '{self.link_to.title}' page"

    panels = [
        FieldPanel("title"),
        FieldPanel("link_to"),
        FieldPanel("result_weighting"),
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
    external_url = fields.URLField(
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
        FieldPanel("preview_image"),
        FieldPanel("link_to"),
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
    # TODO: Remove this after networks reordering!
    subpage_types = ["networks.NetworksHome"]
    base_form_class = HomePageForm

    # Fields
    class PriorityPagesLayout(models.TextChoices):
        __value_regex__ = re.compile(r"L[0-3]_[0-3]")

        def __init__(self, *args):
            if not self.__value_regex__.fullmatch(self.value):
                raise ValueError(
                    "Layout value does not match pattern"
                    f" (value={self.value!r} pattern={self.__value_regex__.pattern!r})"
                )

        L1_0 = "L1_0", "1 card"
        L2_0 = "L2_0", "2 cards"
        L3_0 = "L3_0", "3 cards"
        L1_2 = "L1_2", "1 card then 2 cards"
        L1_3 = "L1_3", "1 card then 3 cards"
        L2_3 = "L2_3", "2 cards then 3 cards"

        def to_page_counts(self) -> list[int]:
            """Return the layout as a list of page counts.

            Examples:
                >>> PriorityPagesLayout.L2_0.to_page_counts()
                [2, 0]

                >>> PriorityPagesLayout.L1_2.to_page_counts()
                [1, 2]
            """
            return [int(x) for x in self.value.removeprefix("L").split("_")]

    priority_pages_layout = models.CharField(
        max_length=4,
        choices=PriorityPagesLayout.choices,
        default=PriorityPagesLayout.L1_3,
    )

    promo_enabled = models.BooleanField("Enable promotion banner", default=False)
    promo_ribbon_text = models.CharField(
        "Promotion banner ribbon text",
        max_length=30,
        null=True,
        blank=True,
        help_text="The text to be display on the ribbon. If empty, the ribbon will be hidden.",
    )
    promo_description = models.TextField(
        "Promotion banner description",
        max_length=200,
        null=True,
        blank=True,
    )
    promo_link_url = fields.URLField(
        "Promotion banner link URL",
        null=True,
        blank=True,
    )
    promo_link_text = models.CharField(
        "Promotion banner link text",
        max_length=50,
        null=True,
        blank=True,
    )
    promo_image = models.ForeignKey(
        to="wagtailimages.Image",
        verbose_name="Promotion banner image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Panels
    promote_panels = []
    content_panels = [
        FieldPanel("priority_pages_layout"),
        InlinePanel(
            "priority_pages",
            label="Priority page",
            heading="Priority pages",
            min_num=1,
            max_num=5,
        ),
        MultiFieldPanel(
            (
                FieldPanel("promo_enabled"),
                FieldPanel("promo_ribbon_text"),
                FieldPanel("promo_description"),
                FieldPanel("promo_link_url"),
                FieldPanel("promo_link_text"),
                FieldPanel("promo_image"),
            ),
            heading="Promotion banner",
        ),
    ]

    def get_template(self, request, *args, **kwargs):
        return "home/home_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)

        # News
        news_items = (
            NewsPage.objects.select_related("preview_image")
            .live()
            .public()
            .annotate_with_comment_count()
            .annotate_with_reaction_count()
        )

        priority_page_ribbon_text_mapping = {
            pp["page_id"]: pp["ribbon_text"]
            for pp in self.priority_pages.all().values("page_id", "ribbon_text")
        }
        priority_page_ids = list(priority_page_ribbon_text_mapping.keys())

        # Load the priority pages, preserving the order.
        priority_pages = [
            p.specific
            for p in ContentPage.objects.select_related("preview_image")
            .filter(id__in=priority_page_ids)
            .annotate_with_comment_count()
            .annotate_with_reaction_count()
            .annotate(ribbon_text=models.F("priority_page__ribbon_text"))
            .order_by("priority_page__sort_order")
        ]

        news_items = news_items.exclude(id__in=priority_page_ids).order_by(
            "-pinned_on_home",
            "-first_published_at",
        )

        events = (
            EventPage.objects.select_related("preview_image")
            .live()
            .public()
            .filter(event_end__gte=timezone.now())
            .exclude(id__in=priority_page_ids)
            .order_by("event_start")
        )

        context.update(
            priority_pages=priority_pages,
            events=events[:6],
            pages_by_news_layout=self.pages_by_news_layout(priority_pages),
            is_empty=priority_pages == [],
            news_items=news_items[:5],
        )

        # GOVUK news
        if not cache.get("homepage_govuk_news"):
            govuk_news_feed_url = "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=department-for-international-trade&organisations%5B%5D=department-for-business-and-trade"

            response = requests.get(
                govuk_news_feed_url,
                timeout=5,
            )
            feed = atoma.parse_atom_bytes(response.content)

            cache.set(
                "homepage_govuk_news",
                feed.entries[:6],
                3000,
            )
        govuk_feed = cache.get("homepage_govuk_news")
        context["govuk_feed"] = [
            {"url": obj.links[0].href, "text": obj.title.value} for obj in govuk_feed
        ]
        context["hide_news"] = settings.HIDE_NEWS

        return context

    def pages_by_news_layout(self, pages) -> Iterator[list[int]]:
        # Turn pages into an iterable that gets consumed as we call `next` on it.
        pages = iter(pages)

        for n in self.PriorityPagesLayout(self.priority_pages_layout).to_page_counts():
            yield [next(pages) for _ in range(n)]

    # Wagtail overrides

    def permissions_for_user(self, user):
        return HomePagePermissionTester(user, self)

    class Meta:
        verbose_name = "Home page"
        permissions = [
            ("can_change_home_page_content", "Can change home page content"),
        ]


class HomePagePermissionTester(PagePermissionTester):
    def __init__(self, user, page):
        super().__init__(user, page)
        self.permission_codenames = [
            perm.permission.codename
            for perm in self.permission_policy.get_cached_permissions_for_user(
                self.user
            )
        ]

    def can_edit(self):
        if "can_change_home_page_content" in self.permission_codenames:
            return True
        return super().can_edit()

    def can_publish(self):
        if "can_change_home_page_content" in self.permission_codenames:
            return True
        return super().can_publish()
