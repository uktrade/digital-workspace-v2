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
    except Exception:
        return

    if not os.getenv("RUN_MAIN"):
        debugpy.listen(("0.0.0.0", 5678))
        sys.stdout.write("debugpy listening on port 5678...\n")

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

    from django.conf import settings

    if settings.DEBUG and settings.ENABLE_DEBUGPY:
        initialize_debugpy()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
