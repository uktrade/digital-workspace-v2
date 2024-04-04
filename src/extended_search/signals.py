from django.db.models.signals import post_delete, post_save

from extended_search import settings
from extended_search.models import Setting


def update_searchsetting_queryset(sender, **kwargs):
    settings.settings_singleton.initialise_db_dict()
    settings.extended_search_settings = settings.settings_singleton.to_dict()


post_save.connect(update_searchsetting_queryset, sender=Setting)
post_delete.connect(update_searchsetting_queryset, sender=Setting)
