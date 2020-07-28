from django.db import models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.search import index
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, TagBase, ItemBase

from content import blocks
from content.forms import NewsCategoryForm

RICH_TEXT_FEATURES = ["bold", "italic", "ol", "ul", "link", "document-link"]


class ContentPage(Page):
    legacy_guid = models.CharField(
        blank=True,
        max_length=255,
        help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True,
        help_text="""Legacy content, pre-conversion"""
    )

    excerpt = models.CharField(max_length=250, blank=True)

    body = StreamField([
        ("heading2", blocks.Heading2Block()),
        ("heading3", blocks.Heading3Block()),
        ("text_section", blocks.TextBlock(
            blank=True,
            features=RICH_TEXT_FEATURES,
            help_text="""Some text to describe what this section is about (will be
            displayed above the list of child pages)"""
        )),
        ("image", blocks.ImageBlock()),
        ("internal_media", blocks.InternalMediaBlock()),
        ("data_table", blocks.DataTableBlock(
            help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
        ))
    ])

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.SearchField("excerpt"),
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
        FieldPanel("excerpt"),
    ]


class NewsCategoryTag(TagBase):
    #free_tagging = False - enable to prevent new tags being added

    class Meta:
        verbose_name = "news tag"
        verbose_name_plural = "news tags"


class TaggedNews(ItemBase):
    tag = models.ForeignKey(
        NewsCategoryTag, related_name="tagged_news", on_delete=models.CASCADE
    )
    content_object = ParentalKey(
        to='content.NewsPage',
        on_delete=models.CASCADE,
        related_name='tagged_news_items'
    )


class NewsPage(ContentPage):
    parent_page_types = ['content.NewsHome']

    # TODO - change to preview image
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    news_categories = ClusterTaggableManager(
        through='content.TaggedNews',
        blank=True,
    )

    promote_panels = ContentPage.promote_panels + [
        FieldPanel('news_categories'),
    ]

    content_panels = ContentPage.content_panels + [
        FieldPanel("hero_image"),
    ]

    def serve(self, request, *args, **kwargs):
        context = super().get_context(request, **kwargs)
        # TODO - store news category after selected and select here
        context["category_form"] = NewsCategoryForm(
            selected_category=""
        )

        if "news_category" in request.POST:
            news_category = request.POST["news_category"]
            news_home = self.get_parent().specific
            url = news_home.url + news_home.reverse_subpage(
                name='news_category', args=(news_category,)
            )
            return redirect(url)

        return render(
            request,
            self.template,
            context
        )

    @property
    def get_categories(self):
        """
        Similar to the authors function above we're returning all the tags that
        are related to the blog post into a list we can access on the template.
        We're additionally adding a URL to access BlogPage objects with that tag
        """
        categories = self.news_categories.all()
        for category in categories:
            category.url = '/' + '/'.join(s.strip('/') for s in [
                self.get_parent().url,
                'tags',
                category.slug
            ])
        return categories


class NewsHome(RoutablePageMixin, Page):
    subpage_types = ["content.ContentPage"]

    def get_child_categories(self):
        categories = []

        news_pages = NewsPage.objects.live().descendant_of(self)

        for page in news_pages:
            # Not tags.append() because we don't want a list of lists
            categories += page.get_categories

        categories = sorted(set(categories))
        return categories

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)

        # Check for category
        if "category" in kwargs:
            category_id = NewsCategoryTag.objects.filter(
                slug=kwargs["category"],
            ).first().pk
            news_items = NewsPage.objects.filter(
                news_categories=category_id,
            ).live().public().order_by('-first_published_at')
        else:
            # Get all posts
            news_items = NewsPage.objects.live().public().order_by('-first_published_at')

        # Paginate all posts by 2 per page
        paginator = Paginator(news_items, 9)
        # Try to get the ?page=x value
        page = request.GET.get("page")

        try:
            # If the page exists and the ?page=x is an int
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            posts = paginator.page(1)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            posts = paginator.page(paginator.num_pages)

        # "posts" will have child pages; you'll need to use .specific in the template
        # in order to access child properties, such as youtube_video_id and subtitle
        context["posts"] = posts

        return context

    @route(r'^category/(?P<category_slug>[-\w]+)/$', name="news_category")
    def past_events(self, request, category_slug):
        request.is_preview = getattr(request, 'is_preview', False)

        return TemplateResponse(
            request,
            self.get_template(request),
            self.get_context(request, category=category_slug)
        )

# class ContentIndexPage(ContentBase):
#     introduction = RichTextField(
#         blank=True,
#         features=RICH_TEXT_FEATURES,
#         help_text="""Some text to describe what this section is about (will be
#         displayed above the list of child pages)"""
#     )
#
#     subpage_types = ["content.ContentIndexPage", "content.ContentPage"]
#
#     search_fields = Page.search_fields + [
#         index.SearchField("excerpt"),
#         index.SearchField("introduction")
#     ]
#
#     content_panels = Page.content_panels + [
#         FieldPanel("excerpt"),
#         FieldPanel("introduction", classname="full")
#     ]

#

