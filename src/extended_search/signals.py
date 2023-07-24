from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from extended_search.models import Setting
from extended_search.settings import extended_search_settings


def update_searchsetting_queryset(sender, **kwargs):
    extended_search_settings.initialise_db_dict()


post_save.connect(update_searchsetting_queryset, sender=Setting)
post_delete.connect(
    update_searchsetting_queryset, sender=Setting
)  # this seems to fire too early? not having an effect...
