from django.db import models

from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed


class Model(models.Model):
    title = models.CharField(max_length=225)


class AbstractModel(Model):
    class Meta:
        abstract = True


class IndexedModel(Indexed, Model):
    ...


class AbstractIndexedModel(IndexedModel):
    class Meta:
        abstract = True


class ChildModel(IndexedModel):
    ...


class StandardIndexedModel(IndexedModel):
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
