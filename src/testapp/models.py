from django.db import models
from wagtail.search.queryset import SearchableQuerySetMixin

from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed, ScoreFunction


class Model(models.Model):
    title = models.CharField(max_length=225)
    age = models.IntegerField()


class AbstractModel(Model):
    class Meta:
        abstract = True


class ModelQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


class IndexedModel(Indexed, Model):
    objects = models.Manager.from_queryset(ModelQuerySet)()


class AbstractIndexedModel(IndexedModel):
    class Meta:
        abstract = True


class ChildModel(IndexedModel): ...


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


class StandardIndexedModelWithScoreFunction(StandardIndexedModel):
    indexed_fields = [
        ScoreFunction(
            "gauss",
            field_name="age",
            origin=0,
            scale=1,
            decay=0.5,
        ),
    ]


class StandardIndexedModelWithScoreFunctionOriginFifty(StandardIndexedModel):
    indexed_fields = [
        ScoreFunction(
            "gauss",
            field_name="age",
            origin=50,
            scale=1,
            decay=0.5,
        ),
    ]


class InheritedStandardIndexedModel(StandardIndexedModel):
    new_age = models.IntegerField()


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


class InheritedStandardIndexedModelWithChangesWithScoreFunction(
    InheritedStandardIndexedModel
):
    indexed_fields = [
        ScoreFunction(
            "gauss",
            field_name="new_age",
            origin=0,
            scale=1,
            decay=0.5,
        ),
    ]
