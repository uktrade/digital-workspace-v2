import os

from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    def run(self, *args, **options):
        if os.getenv("DEBUGPY_ENABLED", "False").lower() == "true":
            if os.getenv("RUN_MAIN") or os.getenv("WERKZEUG_RUN_MAIN"):
                import debugpy

                try:
                    debugpy.listen(("0.0.0.0", 5678))  # noqa: S104
                    self.stdout.write("debugpy: listening on port 5678...\n")
                except Exception as err:
                    self.stderr.write(f"debugpy: failed to initialize {err}\n")

        super().run(*args, **options)
