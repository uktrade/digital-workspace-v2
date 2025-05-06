from django.apps import AppConfig


class CountryFactSheetConfig(AppConfig):
    name = "country_fact_sheet"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
