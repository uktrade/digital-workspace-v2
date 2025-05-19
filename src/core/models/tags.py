from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import ItemBase, TagBase
from wagtail.models.specific import SpecificMixin

from core.panels import FieldPanel
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed
from peoplefinder.widgets import PersonChooser, TeamChooser


def get_default_tag_content_type():
    return ContentType.objects.get_for_model(Tag)


def get_default_tag_content_type_id():
    return get_default_tag_content_type().id


class Tag(SpecificMixin, ClusterableModel, Indexed, TagBase):
    free_tagging = False

    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        related_name="tags",
        on_delete=models.SET(get_default_tag_content_type),
        default=get_default_tag_content_type_id,
    )

    indexed_fields = [
        IndexedField(
            "name",
            tokenized=True,
            autocomplete=True,
        ),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    @property
    def link(self):
        return format_html('<a href="{}">view</a>', self.get_absolute_url())

    def get_absolute_url(self):
        return reverse("tag_index", kwargs={"slug": self.slug})

    def get_edit_url(self):
        raise NotImplementedError


class TagGroup(Tag):
    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name}"


class Campaign(TagGroup):
    def get_edit_url(self):
        return reverse("wagtailsnippets_core_campaign:edit", kwargs={"pk": self.pk})


class TaggedItem(ItemBase):
    class Meta:
        abstract = True
        # NOTE: For some reason a `UniqueConstraint` doesn't work with an `InlinePanel`
        # but a `unique_constraint` does. I think it has something to do with
        # `django-modelcluster` but for now this will have to do.
        unique_together = ("tag", "content_object")

    tag = ParentalKey(
        to=Tag,
        on_delete=models.CASCADE,
        # e.g. taggedpage_set
        related_name="%(class)s_set",
    )

    panels = [
        FieldPanel("tag"),
    ]

    def __str__(self):
        return str(self.content_object)


# Through model
class TaggedPage(TaggedItem):
    content_object = ParentalKey(
        to="content.ContentPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )

    panels = TaggedItem.panels + [
        FieldPanel("content_object"),
    ]


class TaggedPerson(TaggedItem):
    content_object = ParentalKey(
        to="peoplefinder.Person",
        on_delete=models.CASCADE,
        related_name="tagged_people",
    )

    panels = TaggedItem.panels + [
        FieldPanel("content_object", widget=PersonChooser),
    ]


class TaggedTeam(TaggedItem):
    content_object = ParentalKey(
        to="peoplefinder.Team",
        on_delete=models.CASCADE,
        related_name="tagged_teams",
    )

    panels = TaggedItem.panels + [
        FieldPanel("content_object", widget=TeamChooser),
    ]
