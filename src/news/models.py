from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, Paginator
from django.db import models
from django.template.response import TemplateResponse
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.snippets.models import register_snippet

from content.models import BasePage
from extended_search.index import DWIndexedField as IndexedField
from news.forms import CommentForm
from working_at_dit.models import PageWithTopics


UserModel = get_user_model()


class Comment(models.Model):
    legacy_id = models.IntegerField(
        null=True,
    )
    news_page = models.ForeignKey("news.NewsPage", on_delete=models.CASCADE)
    author = models.ForeignKey(
        UserModel, null=True, blank=True, on_delete=models.CASCADE
    )
    legacy_author_name = models.CharField(max_length=255, blank=True, null=True)
    legacy_author_email = models.EmailField(blank=True, null=True)
    content = models.TextField()
    posted_date = models.DateTimeField(default=datetime.now)
    parent = models.ForeignKey(
        "news.Comment",
        on_delete=models.CASCADE,
        null=True,
        related_name="replies",
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.content

    panels = [
        FieldPanel("news_page"),
        FieldPanel("author"),
        FieldPanel("content"),
    ]


@register_snippet
class NewsCategory(models.Model):
    class Meta:
        verbose_name_plural = "Categories"

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )
    category = models.CharField(
        max_length=255,
        unique=True,
    )

    lead_story = models.ForeignKey(
        "news.NewsPage",
        on_delete=models.CASCADE,
        related_name="news_pages",
        null=True,
        blank=True,
    )
    history = history = HistoricalRecords()

    def __str__(self):
        return self.category

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category)
        super(NewsCategory, self).save(*args, **kwargs)

    panels = [
        FieldPanel("category"),
        FieldPanel("lead_story"),
    ]


class NewsPageNewsCategory(models.Model):
    news_page = ParentalKey(
        "news.NewsPage",
        on_delete=models.CASCADE,
        related_name="news_categories",
    )

    news_category = models.ForeignKey(
        "news.NewsCategory",
        on_delete=models.CASCADE,
        related_name="news_pages",
    )

    panels = [
        FieldPanel("news_category"),
    ]

    class Meta:
        unique_together = ("news_page", "news_category")


class NewsPage(PageWithTopics):
    is_creatable = True
    parent_page_types = ["news.NewsHome"]
    subpage_types = []  # Should not be able to create children

    pinned_on_home = models.BooleanField(
        default=False,
    )

    perm_sec_as_author = models.BooleanField(
        default=False,
    )

    allow_comments = models.BooleanField(
        default=True,
    )

    preview_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    featured_on_news_home = models.BooleanField(
        default=False,
        help_text="If checked, this will cause the page to "
        "be the featured article on the news homepage. "
        "Other pages will no longer be marked as the "
        "featured article.",
    )

    @property
    def search_categories(self):
        return " ".join(
            self.news_categories.all().values_list("news_category__category", flat=True)
        )

    indexed_fields = [
        IndexedField(
            "search_categories",
            autocomplete=True,
            tokenized=True,
        ),
        IndexedField(
            "pinned_on_home",
            filter=True,
        ),
    ]

    content_panels = PageWithTopics.content_panels + [  # noqa W504
        FieldPanel("preview_image"),
        InlinePanel("news_categories", label="News categories"),
        FieldPanel("allow_comments"),
        FieldPanel("perm_sec_as_author"),
        FieldPanel("pinned_on_home"),
    ]

    promote_panels = [
        FieldPanel("featured_on_news_home"),
    ] + PageWithTopics.promote_panels

    def save(self, *args, **kwargs):
        # If set as featured article, set all other
        # articles to be not being
        if self.featured_on_news_home:
            NewsPage.objects.exclude(
                slug=self.slug,
            ).update(featured_on_news_home=False)

        return super().save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        comments = Comment.objects.filter(
            news_page=self,
            parent_id=None,
        ).order_by("-posted_date")

        context["comments"] = comments
        context["comment_count"] = Comment.objects.filter(
            news_page=self,
        ).count()

        categories = NewsCategory.objects.all().order_by("category")
        context["categories"] = categories

        return context

    def serve(self, request, *args, **kwargs):
        # Add comment before calling get_context, so it's included
        if "comment" in request.POST:
            comment = request.POST["comment"]
            in_reply_to = request.POST.get("in_reply_to", None)
            Comment.objects.create(
                content=comment,
                author=request.user,
                news_page=self,
                parent_id=in_reply_to,
            )

        context = self.get_context(request, **kwargs)
        context["comment_form"] = CommentForm()

        response = TemplateResponse(request, self.template, context)

        return response


class NewsHome(RoutablePageMixin, BasePage):
    show_in_menus = True
    is_creatable = False

    subpage_types = ["news.NewsPage"]

    @route(r"^$", name="news_home")
    def news_home(self, request):
        request.is_preview = getattr(request, "is_preview", False)
        context = self.get_context(request)

        featured_page = NewsPage.objects.filter(
            featured_on_news_home=True,
        ).first()

        if featured_page:
            context["featured_page"] = featured_page

        response = TemplateResponse(
            request,
            self.get_template(request),
            context,
        )

        return response

    @route(r"^category/(?P<category_slug>[-\w]+)/$", name="news_category")
    def category_home(self, request, category_slug):
        request.is_preview = getattr(request, "is_preview", False)
        context = self.get_context(request, category=category_slug)

        response = TemplateResponse(
            request,
            self.get_template(request),
            context,
        )

        return response

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        context["page_title"] = self.title

        categories = NewsCategory.objects.all().order_by("category")
        context["categories"] = categories

        # Check for category
        if "category" in kwargs:
            category = NewsCategory.objects.filter(
                slug=kwargs["category"],
            ).first()
            news_items = (
                NewsPage.objects.filter(
                    news_categories__news_category_id__in=[
                        category.pk,
                    ],
                )
                .live()
                .public()
                .order_by(
                    "-pinned_on_home",
                    "home_news_order_pages__order",
                    "-first_published_at",
                )
            )

            if category.lead_story:
                news_items = news_items.exclude(
                    pk=category.lead_story.pk,
                )

            context["category"] = category
        else:
            # Get all posts
            news_items = (
                NewsPage.objects.live()
                .public()
                .order_by(
                    "-pinned_on_home",
                    "home_news_order_pages__order",
                    "-first_published_at",
                )
            )

            featured_page = NewsPage.objects.filter(
                featured_on_news_home=True,
            ).first()

            if featured_page:
                news_items = news_items.exclude(
                    pk=featured_page.pk,
                )

        # Paginate all posts by 2 per page
        paginator = Paginator(news_items, 9)
        # Try to get the ?page=x value
        page = int(request.GET.get("page", 1))

        try:
            # If the page exists and the ?page=x is an int
            posts = paginator.page(page)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            posts = paginator.page(paginator.num_pages)

        start = 1
        total_shown = 10

        if paginator.num_pages < total_shown:
            total_shown = paginator.num_pages

        if page > 9:
            start = page - 7
            total_shown = 10

            if (page + 2) > paginator.num_pages:
                start = paginator.num_pages - 9

        context["pagination_range"] = range(start, (start + total_shown))

        # "posts" will have child pages; you'll need to use .specific in the templates
        # in order to access child properties, such as youtube_video_id and subtitle
        context["posts"] = posts

        return context
