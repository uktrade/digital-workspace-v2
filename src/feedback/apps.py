from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    name = "feedback"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
