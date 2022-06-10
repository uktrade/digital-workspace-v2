from django.apps import AppConfig


class PeoplefinderConfig(AppConfig):
    name = "peoplefinder"

    def ready(self):
        from . import signals  # noqa F401
