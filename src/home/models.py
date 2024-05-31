import atoma
import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from waffle import flag_is_active
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail_adminsortable.models import AdminSortable

from content.models import BasePage
from home import FEATURE_HOMEPAGE
from interactions import get_bookmarks, get_recent_page_views
from news.models import NewsPage
from working_at_dit.models import HowDoI


@register_snippet
class HomeNewsOrder(AdminSortable, ClusterableModel):
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

    subpage_types = []

    promote_panels = []

    def get_template(self, request, *args, **kwargs):
        if flag_is_active(request, FEATURE_HOMEPAGE):
            return "home/home_page_new.html"
        return "home/home_page.html"

    def get_context(self, request, *args, **kwargs):
        is_new_homepage = flag_is_active(request, FEATURE_HOMEPAGE)
        context = super(HomePage, self).get_context(request, *args, **kwargs)

        # Quick links
        quick_links = QuickLink.objects.all().order_by("result_weighting", "title")
        if is_new_homepage:
            quick_links = [
                {"url": obj.link_to.get_url(request), "text": obj.title}
                for obj in quick_links
            ]
        context["quick_links"] = quick_links

        # Popular on Digital Workspace
        whats_popular_items = WhatsPopular.objects.all()
        if is_new_homepage:
            whats_popular_items = [
                {"url": obj.link_to.get_url(request), "text": obj.title}
                for obj in whats_popular_items
            ]
        context["whats_popular_items"] = whats_popular_items

        # News
        news_items = (
            NewsPage.objects.live()
            .public()
            .order_by(
                "-pinned_on_home",
                "home_news_order_pages__order",
                "-first_published_at",
            )[:8]
        )
        context["news_items"] = news_items

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
        if is_new_homepage:
            govuk_feed = [
                {"url": obj.links[0].href, "text": obj.title.value}
                for obj in govuk_feed
            ]
        context["govuk_feed"] = govuk_feed
        context["hide_news"] = settings.HIDE_NEWS

        # Personalised page list
        context["bookmarks"] = get_bookmarks(request.user)
        context["recently_viewed"] = get_recent_page_views(
            request.user, limit=10, exclude_pages=[self]
        )

        # # Updates
        # updates = []
        # if request.user.profile.profile_completion < 99:
        #     updates.append(
        #         format_html(
        #             "Please complete <a href='{}'>your profile</a>, it's currently at {}%",
        #             reverse("profile-view", args=[request.user.profile.slug]),
        #             request.user.profile.profile_completion,
        #         )
        #     )
        # for page in get_updated_pages(request.user):
        #     updates.append(
        #         format_html(
        #             "<a href='{}'>{}</a> has been updated",
        #             page.get_url(request),
        #             page,
        #         )
        #     )
        # context["updates"] = updates

        return context
