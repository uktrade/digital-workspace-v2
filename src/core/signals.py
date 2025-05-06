import logging

from django.db.models.signals import pre_save
from simple_history.models import HistoricalChanges


logger = logging.getLogger(__name__)


def model_full_clean(sender, instance, **kwargs):
    if "raw" in kwargs and not kwargs["raw"]:
        instance.full_clean()


def add_validators(app):
    """
    Add pre_save signal to all models in an app.

    This signal will cause validation to run on a model when the `save` method
    is called.
    """
    for model in app.get_models():
        if issubclass(model, HistoricalChanges):
            continue

        logger.info(f"pre_save signal for {model.__name__}")
        pre_save.connect(
            model_full_clean,
            sender=f"{app.name}.{model.__name__}",
        )
