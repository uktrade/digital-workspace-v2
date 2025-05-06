from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "interactions"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
