from django.db import models

from extended_search.index import Indexed


class MockModel(models.Model):
    class Meta:
        abstract = False


class MockAbstractModel(models.Model):
    class Meta:
        abstract = True


class MockIndexedModel(Indexed, models.Model):
    class Meta:
        abstract = False


class MockAbstractIndexedModel(Indexed, models.Model):
    class Meta:
        abstract = True
