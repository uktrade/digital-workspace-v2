from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, Paginator
from django.db import models
from django.template.response import TemplateResponse
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from simple_history.models import HistoricalRecords
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.snippets.models import register_snippet

from content.models import BasePage
from core.panels import FieldPanel, InlinePanel
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import ScoreFunction
from news.forms import CommentForm
from working_at_dit.models import PageWithTopics


UserModel = get_user_model()


class Comment(models.Model):
    legacy_id = models.IntegerField(
        null=True,
    )
    page = models.ForeignKey(
        "content.ContentPage", on_delete=models.CASCADE, related_name="comments"
    )
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
        FieldPanel("page"),
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

    allow_reactions = models.BooleanField(
        default=True,
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
        ScoreFunction(
            "gauss",
            field_name="last_published_at",
            scale="365d",
            offset="14d",
            decay=0.3,
        ),
    ]

    content_panels = PageWithTopics.content_panels + [  # noqa W504
        InlinePanel("news_categories", label="News categories"),
    ]

    settings_panels = [
        FieldPanel("allow_comments"),
        FieldPanel("allow_reactions"),
        FieldPanel("perm_sec_as_author"),
        FieldPanel("pinned_on_home"),
    ]

    def get_comments(self):
        return self.comments.filter(parent_id=None).order_by("-posted_date")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["page"] = (
            NewsPage.objects.annotate_with_comment_count()
            .annotate_with_reaction_count()
            .get(pk=self.pk)
        )
        context["comments"] = self.get_comments()
        context["categories"] = NewsCategory.objects.all().order_by("category")

        return context

    def serve(self, request, *args, **kwargs):
        # Add comment before calling get_context, so it's included
        if "comment" in request.POST:
            print("DEBUG_COMMENT_CREATION")
            print(request.POST)
            print("END_DEBUG_COMMENT_CREATION")
            comment = request.POST["comment"]
            in_reply_to = request.POST.get("in_reply_to", None)
            Comment.objects.create(
                content=comment,
                author=request.user,
                page=self,
                parent_id=in_reply_to,
            )
        # in_reply_to = request.POST.get("edit-commment", None)

        # print("DEBUG_COMMENT_CONTENT")
        # print(request.POST)
        context = self.get_context(request, **kwargs)
        context["comment_form"] = CommentForm()
        context["reply_comment_form"] = CommentForm(auto_id="reply_%s")

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

        news_items = NewsPage.objects.live().public()

        # Check for category
        if "category" in kwargs:
            category = NewsCategory.objects.filter(
                slug=kwargs["category"],
            ).first()
            context["category"] = category

            news_items = news_items.filter(
                news_categories__news_category_id__in=[
                    category.pk,
                ],
            )

            if category.lead_story:
                news_items = news_items.exclude(
                    pk=category.lead_story.pk,
                )

        # Add comment counts
        news_items = (
            news_items.annotate_with_comment_count()
            .annotate_with_reaction_count()
            .order_by(
                "-first_published_at",
            )
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

        context["posts"] = posts

        return context
