from django.apps import AppConfig


class ToolsConfig(AppConfig):
    name = "tools"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
