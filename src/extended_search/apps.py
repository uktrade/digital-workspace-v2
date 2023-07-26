from django.apps import AppConfig
from django.conf import settings

class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        from extended_search.settings import extended_search_settings as search_settings
        import extended_search.signals  # noqa

        search_settings.initialise_field_dict()
        search_settings.initialise_env_dict()
        if settings.APP_ENV != "test":
            search_settings.initialise_db_dict()
