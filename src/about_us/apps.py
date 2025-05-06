from django.apps import AppConfig


class AboutUsConfig(AppConfig):
    name = "about_us"

    def ready(self):
        from core.signals import add_validators

        add_validators(self)
