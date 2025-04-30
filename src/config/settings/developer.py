from .base import *  # noqa


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

# Enable Django Debug Toolbar
DDT_ENABLED = env.bool("DDT_ENABLED", False)  # noqa F405
if DDT_ENABLED:
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    # Add the middleware to the top of the list.
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa F405
    INTERNAL_IPS = [
        "127.0.0.1",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda x: True,
    }

SILK_ENABLED = env.bool("SILK_ENABLED", False)  # noqa F405
if SILK_ENABLED:
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


DEV_TOOLS_ENABLED = env.bool("DEV_TOOLS_ENABLED", True)  # noqa F405

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
