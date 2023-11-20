from django.apps import AppConfig
from django.conf import settings as django_settings


class ExtendedSearchConfig(AppConfig):
    name = "extended_search"

    def ready(self):
        import extended_search.signals  # noqa
        from extended_search import settings

        settings.settings_singleton.initialise_field_dict()
        settings.settings_singleton.initialise_env_dict()
        if django_settings.APP_ENV not in ["test", "build"]:
            settings.settings_singleton.initialise_db_dict()
        settings.extended_search_settings = settings.settings_singleton.to_dict()

        from extended_search.index import get_indexed_models
        from extended_search.managers.query_builder import CustomQueryBuilder

        for model_class in get_indexed_models():
            if hasattr(model_class, "indexed_fields") and model_class.indexed_fields:
                CustomQueryBuilder.build_search_query(model_class, True)
