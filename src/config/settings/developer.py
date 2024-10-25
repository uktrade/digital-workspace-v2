import os

import environ

from .base import *  # noqa


# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
env_file = os.path.join(PROJECT_ROOT_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)
env.read_env()

DEBUG = True

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

INSTALLED_APPS += [  # noqa F405
    "django_extensions",
]

MEDIA_URL = "/media/"
STORAGES["default"][  # noqa F405
    "BACKEND"
] = "django.core.files.storage.FileSystemStorage"  # noqa F405
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

try:
    # Add django-silk for profiling
    import silk  # noqa F401

    INSTALLED_APPS += [  # noqa F405
        "silk",
    ]
    MIDDLEWARE += [  # noqa F405
        "silk.middleware.SilkyMiddleware",
    ]
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(  # noqa F405
        PROJECT_ROOT_DIR,  # noqa F405
        "profiler_results",
    )
    SILKY_META = True
except ModuleNotFoundError:
    ...


DEV_TOOLS_ENABLED = env.bool("DEV_TOOLS_ENABLED", True)

if DEV_TOOLS_ENABLED:
    # remove Django Staff SSO Client for local login
    MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")
    AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")  # noqa F405
    # ... and add Dev Tools
    DEV_TOOLS_LOGIN_URL = "dev_tools:login"
    DEV_TOOLS_DEFAULT_USER = 1
    # INSTALLED_APPS += ["dev_tools"]
    TEMPLATES[0]["OPTIONS"]["context_processors"].append(  # noqa F405
        "dev_tools.context_processors.dev_tools"
    )
    MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")
