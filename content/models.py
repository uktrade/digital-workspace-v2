from django.db import models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.search import index



from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, TagBase, ItemBase

from . import blocks

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

    search_fields = Page.search_fields + [
        index.SearchField("excerpt"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("excerpt"),
    ]

    body = StreamField([
        ("heading", blocks.HeadingBlock()),
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
        index.SearchField("body")
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel("body")
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

    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    tags = ClusterTaggableManager(
        through='content.TaggedNews',
        blank=True,
    )

    promote_panels = ContentPage.promote_panels + [
        FieldPanel('tags'),
    ]

    @property
    def get_tags(self):
        """
        Similar to the authors function above we're returning all the tags that
        are related to the blog post into a list we can access on the template.
        We're additionally adding a URL to access BlogPage objects with that tag
        """
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/' + '/'.join(s.strip('/') for s in [
                self.get_parent().url,
                'tags',
                tag.slug
            ])
        return tags


class NewsHome(Page):
    subpage_types = ["content.ContentPage"]

    def get_child_tags(self):
        tags = []

        news_pages = NewsPage.objects.live().descendant_of(self)

        for page in news_pages:
            # Not tags.append() because we don't want a list of lists
            tags += page.get_tags

        tags = sorted(set(tags))
        return tags

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        # Get all posts
        all_news = NewsPage.objects.live().public().order_by('-first_published_at')
        # Paginate all posts by 2 per page
        paginator = Paginator(all_news, 9)
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

