from django.apps import AppConfig


class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        from extended_search.settings import extended_search_settings as settings

        settings.initialise_field_dict()
        settings.initialise_env_dict()
