from django.apps import AppConfig


class IntranetProfileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "intranet_profile"

    def ready(self) -> None:
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals  # noqa: F401
