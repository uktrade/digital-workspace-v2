from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = "events"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
