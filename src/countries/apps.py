from django.apps import AppConfig


class CountriesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "countries"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
