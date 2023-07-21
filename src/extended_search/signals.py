from django.db.models.signals import post_save
from django.dispatch import receiver

from extended_search.models import Setting
from extended_search.settings import extended_search_settings


@receiver(post_save, sender=Setting)
def update_searchsetting_queryset(sender, instance, **kwargs):
    extended_search_settings.initialise_db_dict()
