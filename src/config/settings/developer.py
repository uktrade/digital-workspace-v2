from .base import *  # noqa

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

# Set to True if you need to upload documents and you are not running
# the ClamAV service locally.
SKIP_CLAM_AV_FILE_UPLOAD = False

if SKIP_CLAM_AV_FILE_UPLOAD:
    FILE_UPLOAD_HANDLERS = ("django_chunk_upload_handlers.s3.S3FileUploadHandler",)

INSTALLED_APPS += [  # noqa F405
    "django_extensions",
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
