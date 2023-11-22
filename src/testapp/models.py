from django.db import models

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
