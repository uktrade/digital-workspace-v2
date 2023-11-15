from .base import *  # noqa

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

# Set to True if you need to upload documents and you are not running
# the ClamAV service locally.
SKIP_CLAM_AV_FILE_UPLOAD = False

if SKIP_CLAM_AV_FILE_UPLOAD:
    FILE_UPLOAD_HANDLERS = ("django_chunk_upload_handlers.s3.S3FileUploadHandler",)

INSTALLED_APPS += [
    "django_extensions",
    "silk",
]

# Add django-silk for profiling
MIDDLEWARE += [
    "silk.middleware.SilkyMiddleware",
]

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(PROJECT_ROOT_DIR, "profiler_results")
SILKY_META = True
