#!/usr/bin/env python
import os
import sys


def initialize_debugpy():
    try:
        import debugpy
    except ImportError:
        sys.stdout.write(
            "debugpy is not installed, please install it with: pip install debugpy\n"
        )
        return

    if not os.getenv("RUN_MAIN"):
        debugpy.listen(("0.0.0.0", 5678))
        sys.stdout.write("debugpy listening on port 5678...\n")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    ENABLE_DEBUGPY = os.getenv("ENABLE_DEBUGPY")
    if ENABLE_DEBUGPY and ENABLE_DEBUGPY.lower() == "true":
        initialize_debugpy()
    main()
