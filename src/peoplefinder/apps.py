from django.apps import AppConfig


class PeoplefinderConfig(AppConfig):
    name = "peoplefinder"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
