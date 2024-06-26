from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from modelcluster.fields import ParentalKey
from taggit.models import ItemBase, TagBase

from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed


class Tag(Indexed, TagBase):
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


class TaggedItem(ItemBase):
    class Meta:
        abstract = True
        # NOTE: For some reason a `UniqueConstraint` doesn't work with an `InlinePanel`
        # but a `unique_constraint` does. I think it has something to do with
        # `django-modelcluster` but for now this will have to do.
        unique_together = ("tag", "content_object")

    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE,
        # e.g. taggedpage_set
        related_name="%(class)s_set",
    )


# Through model
class TaggedPage(TaggedItem):
    content_object = ParentalKey(
        to="content.ContentPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


# TODO: TaggedPerson
# TODO: TaggedTeam
