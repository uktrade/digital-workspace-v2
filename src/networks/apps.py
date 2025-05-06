from django.apps import AppConfig


class NetworksConfig(AppConfig):
    name = "networks"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
