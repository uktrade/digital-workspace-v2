import html
import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Func, OuterRef, Q, Subquery
from django.forms import widgets
from django.utils import timezone
from django.utils.html import strip_tags
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import (
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
    TitleFieldPanel,
)
from wagtail.admin.widgets.slug import SlugInput
from wagtail.blocks.stream_block import StreamValue
from wagtail.fields import StreamField
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.snippets.models import register_snippet
from wagtail.utils.decorators import cached_classmethod

import dw_design_system.dwds.components as dwds_blocks
from content import blocks as content_blocks
from content.forms import BasePageForm
from content.utils import (
    get_search_content_for_block,
    manage_excluded,
    manage_pinned,
    truncate_words_and_chars,
)
from content.validators import validate_description_word_count
from core.panels import FieldPanel, InlinePanel
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed, RelatedFields
from peoplefinder.models import Person
from peoplefinder.widgets import PersonChooser, TeamChooser
from user.models import User as UserModel


logger = logging.getLogger(__name__)

User = get_user_model()


def strip_tags_with_newlines(string: str) -> str:
    spaced = string.replace("><", ">\n<")
    return strip_tags(spaced)


@register_snippet
class Theme(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    summary = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.title

    panels = [
        FieldPanel("title"),
        FieldPanel("summary"),
    ]

    class Meta:
        ordering = ["-title"]


class BasePageQuerySet(PageQuerySet):
    def restricted_q(self, restriction_type):
        from wagtail.models import BaseViewRestriction, PageViewRestriction

        if isinstance(restriction_type, str):
            restriction_type = [
                restriction_type,
            ]

        RESTRICTION_CHOICES = BaseViewRestriction.RESTRICTION_CHOICES
        types = [t for t, _ in RESTRICTION_CHOICES if t in restriction_type]

        q = Q()
        for restriction in (
            PageViewRestriction.objects.filter(restriction_type__in=types)
            .select_related("page")
            .all()
        ):
            q |= self.descendant_of_q(restriction.page, inclusive=True)

        return q if q else Q(pk__in=[])

    def public_or_login(self):
        return self.exclude(self.restricted_q(["password", "groups"]))

    def pinned_q(self, query):
        pinned = SearchPinPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(pinned.values("object_id")))

    def pinned(self, query):
        return self.filter(self.pinned_q(query))

    def not_pinned(self, query):
        return self.exclude(self.pinned_q(query))

    def exclusions_q(self, query):
        exclusions = SearchExclusionPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(exclusions.values("object_id")))

    def exclusions(self, query):
        return self.filter(self.exclusions_q(query))

    def annotate_with_total_views(self):
        return self.annotate(
            total_views=models.Sum(
                "interactions_recentpageviews__count",
                distinct=True,
            )
        )

    def annotate_with_unique_views_all_time(self):
        return self.annotate(
            unique_views_all_time=models.Count(
                "interactions_recentpageviews",
                distinct=True,
            )
        )

    def annotate_with_unique_views_past_month(self):
        return self.annotate(
            unique_views_past_month=models.Count(
                "interactions_recentpageviews",
                filter=Q(
                    interactions_recentpageviews__updated_at__gte=timezone.now()
                    - timezone.timedelta(weeks=4)
                ),
                distinct=True,
            )
        )

    def order_by_most_recent_unique_views_past_month(self):
        return self.annotate_with_unique_views_past_month().order_by(
            "-unique_views_past_month"
        )


class BasePage(Page, Indexed):
    class Meta:
        permissions = [
            ("view_info_page", "Can view the info page in the Wagtail admin"),
        ]

    objects = PageManager.from_queryset(BasePageQuerySet)()
    base_form_class = BasePageForm

    legacy_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    confirmed_needed_at = models.DateTimeField(default=None, null=True, blank=True)

    archive_notification_sent_at = models.DateTimeField(
        default=None, null=True, blank=True
    )

    page_updates = StreamField(
        [
            ("page_update", content_blocks.PageUpdate()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
        help_text="Tell readers about page important page changes.",
    )

    page_author = models.ForeignKey(
        "peoplefinder.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If no page author is selected, the page owner will be shown instead",
    )

    page_author_name = models.CharField(
        null=True,
        blank=True,
        help_text="If the person doesn't have an active profile on the intranet, you can manually enter their name here",
    )

    page_author_role = models.ForeignKey(
        "peoplefinder.TeamMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Choose the page author's job role. If you do not want to show a job role, choose 'Hide role'.",
    )

    page_author_show_team = models.BooleanField(
        default=False,
        help_text="Choose this option to show the team for the selected role",
    )

    on_behalf_of_person = models.ForeignKey(
        "peoplefinder.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="on_behalf_of",
        help_text="Select someone with a profile on the Intranet",
    )

    on_behalf_of_team = models.ForeignKey(
        "peoplefinder.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="on_behalf_of",
    )

    on_behalf_of_network = models.ForeignKey(
        "networks.Network",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="on_behalf_of",
    )

    on_behalf_of_external = models.CharField(
        blank=True,
        null=True,
        help_text="Enter the name of someone without an Intranet profile",
    )

    promote_panels = []
    content_panels = [
        TitleFieldPanel("title"),
    ]
    publishing_panels = [
        FieldPanel("page_author", widget=PersonChooser),
        FieldPanel("page_author_role"),
        FieldPanel("page_author_show_team"),
        MultiFieldPanel(
            [
                FieldPanel("on_behalf_of_person", widget=PersonChooser),
                FieldPanel("on_behalf_of_external"),
                FieldPanel("on_behalf_of_team", widget=TeamChooser),
                FieldPanel("on_behalf_of_network"),
            ],
            heading="On Behalf Of",
            help_text=(
                "Provide a value for one of the following fields if the author"
                " of this page is posting on behalf of someone else."
            ),
        ),
        FieldPanel("page_updates"),
    ]

    tabbed_interface_objects = [
        ("content_panels", "Content"),
        ("promote_panels", "Promote"),
        ("settings_panels", "Settings"),
        ("publishing_panels", "Publishing"),
    ]

    def fill_page_author_name(self) -> None:
        author = self.get_author()

        if isinstance(author, str) and self.page_author_name != author:
            self.page_author_name = author
            return

        if isinstance(author, Person) and self.page_author_name != author.full_name:
            self.page_author_name = author.full_name
            return

    def sort_page_updates(self) -> None:
        """
        Reorder the `page_updates` blocks by the `update_time` value from most
        recent to oldest
        """
        self.page_updates = StreamValue(
            self.page_updates.stream_block,
            sorted(
                self.page_updates,
                key=lambda x: x.value["update_time"],
                reverse=True,
            ),
        )

        return None

    def full_clean(self, *args, **kwargs):
        self.fill_page_author_name()
        self.sort_page_updates()
        super().full_clean(*args, **kwargs)

        on_behalf_of_fields = [
            "on_behalf_of_person",
            "on_behalf_of_external",
            "on_behalf_of_team",
            "on_behalf_of_network",
        ]
        on_behalf_of_errors = {
            field_name: "Only one 'On Behalf of' field may be set."
            for field_name in on_behalf_of_fields
            if getattr(self, field_name, False)
        }
        if len(on_behalf_of_errors) > 1:
            raise ValidationError(on_behalf_of_errors)

    @cached_classmethod
    def get_edit_handler(cls):
        return TabbedInterface(
            [
                ObjectList(getattr(cls, field_name), heading=heading)
                for field_name, heading in cls.tabbed_interface_objects
            ]
        ).bind_to_model(cls)

    @property
    def published_date(self):
        return self.last_published_at

    def get_author(self) -> Optional[Person | str]:
        if self.page_author:
            return self.page_author

        if self.page_author_name:
            return self.page_author_name

        # TODO: Remove this in future ticket when we strip out the "perm_sec_as_author" field.
        if getattr(self, "perm_sec_as_author", False) and settings.PERM_SEC_NAME:
            return settings.PERM_SEC_NAME

        if first_publisher := self.get_first_publisher():
            try:
                return first_publisher.profile
            except User.profile.RelatedObjectDoesNotExist:
                pass

        if self.owner:
            try:
                return self.owner.profile
            except User.profile.RelatedObjectDoesNotExist:
                pass

        return None

    def get_first_publisher(self) -> Optional[UserModel]:
        """Return the first publisher of the page or None."""
        first_revision_with_user = (
            self.revisions.exclude(user=None).order_by("created_at", "id").first()
        )

        if first_revision_with_user:
            return first_revision_with_user.user

        return None

    @property
    def days_since_last_published(self):
        if self.last_published_at:
            result = timezone.now() - self.last_published_at
            return result.days
        return None

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        page_updates_table = []

        for block in self.page_updates:
            page_update = {
                "update_time": block.value["update_time"],
                "person": None,
                "note": None,
            }
            if page_update_person := block.value.get("person"):
                page_update["person"] = page_update_person
            if page_update_note := block.value.get("note"):
                page_update["note"] = page_update_note

            page_updates_table.append(page_update)

        # Build first published update
        if self.first_published_at:
            first_publisher_profile = None
            if first_publisher := self.get_first_publisher():
                try:
                    first_publisher_profile = first_publisher.profile
                except User.profile.RelatedObjectDoesNotExist:
                    pass

            page_updates_table.append(
                {
                    "update_time": self.first_published_at,
                    "person": first_publisher_profile,
                    "note": "Page published",
                }
            )

        context["page_updates_table"] = page_updates_table
        return context


class ContentPageQuerySet(BasePageQuerySet):
    def annotate_with_reaction_count(self):
        return self.annotate(
            reaction_count=models.Count("interactions_pagereactions", distinct=True)
        )

    def annotate_with_comment_count(self):
        from news.models import Comment

        return self.annotate(
            comment_count=Subquery(
                Comment.objects.filter(
                    models.Q(
                        models.Q(parent__is_visible=True)
                        | models.Q(parent__isnull=True)
                    ),
                    is_visible=True,
                    page=OuterRef("id"),
                )
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
        )


class ContentOwnerMixin(models.Model):
    tabbed_interface_objects = BasePage.tabbed_interface_objects + [
        ("content_owner_panels", "Content owner"),
    ]

    content_owner = models.ForeignKey(
        "peoplefinder.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    content_contact_email = models.EmailField(
        help_text="Contact email shown on article, this could be the content owner or a team inbox",
        null=True,
        blank=False,
    )

    content_owner_panels = [
        FieldPanel("content_owner", widget=PersonChooser),
        FieldPanel("content_contact_email"),
    ]

    # This should be imported in the model that uses this mixin, e.g: Network.indexed_fields = [ ... ] + ContentOwnerMixin.indexed_fields
    indexed_fields = [
        RelatedFields(
            "content_owner",
            [
                IndexedField("first_name", explicit=True),
                IndexedField("preferred_first_name", explicit=True),
                IndexedField("last_name", explicit=True),
            ],
        ),
        IndexedField("content_contact_email", explicit=True),
    ]

    class Meta:
        abstract = True

    @classmethod
    def get_all_subclasses(cls):
        subclasses = []
        direct_subclasses = cls.__subclasses__()

        for direct_subclass in direct_subclasses:
            subclasses.append(direct_subclass)
            subclasses.extend(direct_subclass.get_all_subclasses())

        return subclasses


class SearchFieldsMixin(models.Model):
    """
    Specific fields and settings to manage search. Extra fields are generally
    defined to make custom and specific indexing as defined in /docs/search.md

    Usage:
    - Add this mixin to a model
    - Define the fields that should be indexed in search_stream_fields.
      Example: ["body"]
    - Add SearchFieldsMixin.indexed_fields to the Model's indexed_fields list
    - Run self._generate_search_field_content() in full_clean() to generate
      search fields
    """

    class Meta:
        abstract = True

    search_stream_fields: list[str] = []

    search_title = models.CharField(
        max_length=255,
    )
    search_headings = models.TextField(
        blank=True,
        null=True,
    )
    search_content = models.TextField(
        blank=True,
        null=True,
    )

    def _generate_search_field_content(self):
        self.search_title = self.title
        search_headings = []
        search_content = []

        for stream_field_name in self.search_stream_fields:
            stream_field = getattr(self, stream_field_name)
            for stream_child in stream_field:
                block_search_headings, block_search_content = (
                    get_search_content_for_block(stream_child.block, stream_child.value)
                )
                search_headings += block_search_headings
                search_content += block_search_content

        self.search_headings = " ".join(search_headings)
        self.search_content = " ".join(search_content)

    indexed_fields = [
        IndexedField(
            "search_title",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=5.0,
        ),
        IndexedField(
            "search_headings",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=3.0,
        ),
        IndexedField(
            "search_content",
            tokenized=True,
            explicit=True,
        ),
    ]


class ContentPage(SearchFieldsMixin, BasePage):
    objects = PageManager.from_queryset(ContentPageQuerySet)()

    is_creatable = False
    show_in_menus = True
    search_stream_fields = ["body"]

    legacy_guid = models.CharField(
        blank=True, null=True, max_length=255, help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True, null=True, help_text="""Legacy content, pre-conversion"""
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="This should not be more than 30 words.",
        validators=[validate_description_word_count],
    )

    preview_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    body = StreamField(
        [
            ("heading2", content_blocks.Heading2Block()),
            ("heading3", content_blocks.Heading3Block()),
            ("heading4", content_blocks.Heading4Block()),
            ("heading5", content_blocks.Heading5Block()),
            (
                "text_section",
                content_blocks.TextBlock(
                    blank=True,
                    help_text="""Some text to describe what this section is about (will be displayed above the list of child pages)""",
                ),
            ),
            ("image", content_blocks.ImageBlock()),
            ("image_with_text", content_blocks.ImageWithTextBlock()),
            ("quote", content_blocks.QuoteBlock()),
            (
                "embed_video",
                content_blocks.EmbedVideoBlock(help_text="""Embed a video"""),
            ),
            (
                "media",
                content_blocks.InternalMediaBlock(
                    help_text="""Link to a media block"""
                ),
            ),
            (
                "data_table",
                content_blocks.DataTableBlock(
                    help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
                ),
            ),
            ("person_banner", content_blocks.PersonBanner()),
        ],
        use_json_field=True,
    )

    excerpt = models.CharField(
        max_length=700,
        blank=True,
        null=True,
        help_text=(
            "A summary of the page to be shown in search results. (making this"
            " field empty will result in an autogenerated excerpt)"
        ),
    )

    pinned_phrases = models.CharField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="A comma separated list of pinned keywords and phrases. "
        "Do not use quotes for phrases. The page will be pinned "
        "to the first page of search results for these terms.",
    )

    excluded_phrases = models.CharField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="A comma separated list of excluded keywords and phrases. "
        "Do not use quotes for phrases. The page will be removed "
        "from search results for these terms",
    )

    useful_links = StreamField(
        [
            ("useful_links", content_blocks.UsefulLinkBlock()),
        ],
        blank=True,
        null=True,
    )

    spotlight_page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    #
    # Topics
    # This would ideally belong on PageWithTopics, but the Network model uses it
    # and it's not worth the effort to refactor it.
    #

    @property
    def topics(self):
        from working_at_dit.models import Topic

        # This needs to be a list comprehension to work nicely with modelcluster.
        topic_ids = [page_topic.topic.pk for page_topic in self.page_topics.all()]
        return Topic.objects.filter(pk__in=topic_ids)

    @property
    def topic_titles(self):
        return [topic.title for topic in self.topics]

    #
    # Search
    # Specific fields and settings to manage search. Extra fields are generally
    # defined to make custom and specific indexing as defined in /docs/search.md
    #

    indexed_fields = SearchFieldsMixin.indexed_fields + [
        IndexedField(
            "excerpt",
            tokenized=True,
            explicit=True,
            boost=2.0,
        ),
        IndexedField("is_creatable", filter=True),
        IndexedField(
            "description",
            tokenized=True,
            explicit=True,
        ),
    ]

    #
    # Wagtail admin configuration
    #

    subpage_types = []

    content_panels = BasePage.content_panels + [
        FieldPanel("description"),
        FieldPanel("body"),
        FieldPanel("excerpt", widget=widgets.Textarea),
        FieldPanel("preview_image"),
        InlinePanel("tagged_items", label="Tags"),
    ]

    promote_panels = [
        FieldPanel("slug", widget=SlugInput),
        FieldPanel("show_in_menus"),
        FieldPanel("pinned_phrases"),
        FieldPanel("excluded_phrases"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        tag_set = []
        # TODO: Enable when we want to show tags to users.
        # for tagged_item in self.tagged_items.select_related("tag").all():
        #     tag_set.append(tagged_item.tag)
        context["tag_set"] = tag_set

        return context

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()
        if self.excerpt is None:
            self._generate_excerpt()

        super().full_clean(*args, **kwargs)

    def _generate_excerpt(self):
        content = "".join(
            [str(b.value) for b in self.body if b.block_type == "text_section"]
        )
        self.excerpt = truncate_words_and_chars(
            text=html.unescape(strip_tags_with_newlines(content)),
        )

    def save(self, *args, **kwargs):
        if self.excerpt is None:
            self._generate_excerpt()

        if self.id:
            manage_excluded(self, self.excluded_phrases)
            manage_pinned(self, self.pinned_phrases)

        return super().save(*args, **kwargs)


class SearchKeywordOrPhrase(models.Model):
    keyword_or_phrase = models.CharField(max_length=1000)
    # TODO: Remove historical records.
    history = HistoricalRecords()


class SearchKeywordOrPhraseQuerySet(models.QuerySet):
    def filter_by_query(self, query):
        from search.utils import split_query

        query_parts = split_query(query)
        return self.filter(search_keyword_or_phrase__keyword_or_phrase__in=query_parts)


class NavigationPage(SearchFieldsMixin, BasePage):
    template = "content/navigation_page.html"

    search_stream_fields: list[str] = ["primary_elements", "secondary_elements"]

    primary_elements = StreamField(
        [
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        blank=True,
    )

    secondary_elements = StreamField(
        [
            ("dw_curated_page_links", dwds_blocks.CustomPageLinkListBlock()),
            ("dw_tagged_page_list", dwds_blocks.TaggedPageListBlock()),
            ("dw_cta", dwds_blocks.CTACardBlock()),
            ("dw_engagement_card", dwds_blocks.EngagementCardBlock()),
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        blank=True,
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("primary_elements"),
        FieldPanel("secondary_elements"),
    ]

    indexed_fields = SearchFieldsMixin.indexed_fields + [
        IndexedField("primary_elements"),
        IndexedField("secondary_elements"),
    ]

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        return context

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()
        super().full_clean(*args, **kwargs)


class SectorPage(SearchFieldsMixin, BasePage):
    template = "content/sector_page.html"

    search_stream_fields: list[str] = [
        "sectors",
    ]

    body = StreamField(
        [
            ("heading2", content_blocks.Heading2Block()),
            ("heading3", content_blocks.Heading3Block()),
            ("heading4", content_blocks.Heading4Block()),
            ("heading5", content_blocks.Heading5Block()),
            (
                "text_section",
                content_blocks.TextBlock(
                    blank=True,
                    help_text="""Some text to describe what this section is about (will be displayed above the list of child pages)""",
                ),
            ),
            ("image", content_blocks.ImageBlock()),
            ("image_with_text", content_blocks.ImageWithTextBlock()),
            ("quote", content_blocks.QuoteBlock()),
            (
                "embed_video",
                content_blocks.EmbedVideoBlock(help_text="""Embed a video"""),
            ),
            (
                "media",
                content_blocks.InternalMediaBlock(
                    help_text="""Link to a media block"""
                ),
            ),
            (
                "data_table",
                content_blocks.DataTableBlock(
                    help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
                ),
            ),
            ("person_banner", content_blocks.PersonBanner()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
    )

    sectors = StreamField(
        [
            ("dw_sector_card", dwds_blocks.SectorCardBlock()),
        ],
        blank=True,
    )

    # page_links = StreamField(
    #     [
    #         ("dw_sector_card", dwds_blocks.CustomPageLinkListBlock()),
    #     ],
    #     blank=True,
    # )

    content_panels = BasePage.content_panels + [
        FieldPanel("body"),
        FieldPanel("sectors"),
        # FieldPanel("page_links"),
    ]

    indexed_fields = SearchFieldsMixin.indexed_fields + [
        IndexedField("sectors"),
    ]

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        return context

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()
        super().full_clean(*args, **kwargs)


class SearchExclusionPageLookUp(models.Model):
    objects = SearchKeywordOrPhraseQuerySet.as_manager()

    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    # TODO: Remove historical records.
    history = HistoricalRecords()


class SearchPinPageLookUp(models.Model):
    objects = SearchKeywordOrPhraseQuerySet.as_manager()

    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    # TODO: Remove historical records.
    history = HistoricalRecords()


class BlogIndex(BasePage):
    template = "content/blog_index.html"
    subpage_types = [
        "content.BlogPost",
    ]
    is_creatable = False

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = self.get_children().live().public().order_by("title")
        return context


class BlogPost(ContentPage):
    template = "content/blog_post.html"
    subpage_types = []
    is_creatable = True

    def get_template(self, request, *args, **kwargs):
        return self.template
