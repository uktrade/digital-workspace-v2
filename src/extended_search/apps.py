from django.apps import AppConfig


class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        from extended_search.settings import extended_search_settings as search_settings
        import extended_search.signals  # noqa

        search_settings.initialise_field_dict()
        search_settings.initialise_env_dict()
        search_settings.initialise_db_dict()
