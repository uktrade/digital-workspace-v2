from django.apps import AppConfig


class HomeConfig(AppConfig):
    name = "home"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
