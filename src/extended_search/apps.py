from django.apps import AppConfig
from django.conf import settings


class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        import extended_search.signals  # noqa
        from extended_search.settings import settings_singleton as search_settings_obj

        search_settings_obj.initialise_field_dict()
        search_settings_obj.initialise_env_dict()
        if settings.APP_ENV not in ["test", "build"]:
            search_settings_obj.initialise_db_dict()
