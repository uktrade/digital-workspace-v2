from django.core.management import call_command

from search.search import ModelSearchVector
from testapp.models import (
    InheritedStandardIndexedModelWithScoreFunction,
    InheritedStandardIndexedModelWithScoreFunctionOriginFifty,
)


class CustomSearchVector(ModelSearchVector):
    model = InheritedStandardIndexedModelWithScoreFunction


def test_scorefunction_closer_to_zero_is_better(db, mocker):
    obj1 = InheritedStandardIndexedModelWithScoreFunction(
        title="Title 1",
        age=10,
    )
    obj1.save()
    obj2 = InheritedStandardIndexedModelWithScoreFunction(
        title="Title 2",
        age=20,
    )
    obj2.save()

    # Re-index the objects
    call_command("update_index")

    # Search for the objects
    request = mocker.Mock()
    results = CustomSearchVector(request).search("title")

    # Check the order of the objects
    assert len(results) == 2
    assert results[0].pk == obj1.pk
    assert results[1].pk == obj2.pk


def test_scorefunction_closer_to_fifty_is_better(db, mocker):
    obj1 = InheritedStandardIndexedModelWithScoreFunctionOriginFifty(
        title="Title 1",
        age=10,
    )
    obj1.save()
    obj2 = InheritedStandardIndexedModelWithScoreFunctionOriginFifty(
        title="Title 2",
        age=40,
    )
    obj2.save()

    # Re-index the objects
    call_command("update_index")

    # Search for the objects
    request = mocker.Mock()
    CustomSearchVector.model = InheritedStandardIndexedModelWithScoreFunctionOriginFifty
    results = CustomSearchVector(request).search("title")

    # Check the order of the objects
    assert len(results) == 2
    assert results[0].pk == obj2.pk
    assert results[1].pk == obj1.pk
