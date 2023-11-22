from django.db import models

from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed


class Model(models.Model):
    ...


class AbstractModel(models.Model):
    class Meta:
        abstract = True


class IndexedModel(Indexed, models.Model):
    ...


class AbstractIndexedModel(Indexed, models.Model):
    class Meta:
        abstract = True


class StandardIndexedModel(IndexedModel):
    title = models.CharField(max_length=255)

    indexed_fields = [
        IndexedField(
            "title",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=5.0,
        ),
    ]


class InheritedStandardIndexedModel(StandardIndexedModel):
    ...


class InheritedStandardIndexedModelWithChanges(StandardIndexedModel):
    indexed_fields = [
        IndexedField(
            "title",
            tokenized=True,
            explicit=False,
            fuzzy=False,
            boost=50.0,
        ),
    ]
