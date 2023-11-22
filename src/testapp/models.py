from django.db import models

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
