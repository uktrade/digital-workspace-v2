from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import ItemBase, TagBase

from core.panels import FieldPanel
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed
from peoplefinder.widgets import PersonChooser


class Tag(ClusterableModel, Indexed, TagBase):
    free_tagging = False

    indexed_fields = [
        IndexedField(
            "name",
            tokenized=True,
            autocomplete=True,
        ),
    ]

    @property
    def link(self):
        return format_html('<a href="{}">view</a>', self.get_absolute_url())

    def get_absolute_url(self):
        return reverse("tag_index", kwargs={"slug": self.slug})


class TagGroup(Tag):
    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name}"


class Campaign(TagGroup): ...


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

    def __str__(self):
        return str(self.content_object)


# Through model
class TaggedPage(TaggedItem):
    content_object = ParentalKey(
        to="content.ContentPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )

    panels = [
        FieldPanel("content_object"),
    ]


class TaggedPerson(TaggedItem):
    content_object = ParentalKey(
        to="peoplefinder.Person",
        on_delete=models.CASCADE,
        related_name="tagged_people",
    )

    panels = [
        FieldPanel("content_object", widget=PersonChooser),
    ]


class TaggedTeam(TaggedItem):
    content_object = ParentalKey(
        to="peoplefinder.Team",
        on_delete=models.CASCADE,
        related_name="tagged_teams",
    )
