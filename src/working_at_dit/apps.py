from django.apps import AppConfig


class WorkingAtDitConfig(AppConfig):
    name = "working_at_dit"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
