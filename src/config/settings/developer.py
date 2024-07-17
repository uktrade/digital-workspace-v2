from .base import *  # noqa

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

INSTALLED_APPS += [  # noqa F405
    "django_extensions",
]

MEDIA_URL = "/media/"
STORAGES["default"]["BACKEND"] = "django.core.files.storage.FileSystemStorage"  # noqa F405
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
