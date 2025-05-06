from django.apps import AppConfig


class NewsConfig(AppConfig):
    name = "news"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
