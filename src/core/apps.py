from django.apps import AppConfig
from django.core.cache import cache
from django.db.models.signals import post_save


def clear_external_link_settings_cache(sender, **kwargs):
    from core.utils import EXTENDED_LINKS_SETTINGS_CACHE

    cache.delete(EXTENDED_LINKS_SETTINGS_CACHE["keys"]["exclude_domains"])
    cache.delete(EXTENDED_LINKS_SETTINGS_CACHE["keys"]["domain_mapping"])


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
        post_save.connect(
            clear_external_link_settings_cache, sender="core.ExternalLinkSetting"
        )
