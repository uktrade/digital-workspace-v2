from django.apps import AppConfig
from django.conf import settings as django_settings


class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        import extended_search.signals  # noqa
        from extended_search import query_builder, settings

        settings.settings_singleton.initialise_field_dict()
        settings.settings_singleton.initialise_env_dict()
        if django_settings.APP_ENV not in ["test", "build"]:
            settings.settings_singleton.initialise_db_dict()
        settings.extended_search_settings = settings.settings_singleton.to_dict()
        query_builder.extended_search_settings = settings.extended_search_settings
