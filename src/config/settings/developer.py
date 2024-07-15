from .base import *  # noqa

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

# Set to True if you need to upload documents and you are not running
# the ClamAV service locally.
SKIP_CLAM_AV_FILE_UPLOAD = False

if SKIP_CLAM_AV_FILE_UPLOAD:
    FILE_UPLOAD_HANDLERS = ("django_chunk_upload_handlers.s3.S3FileUploadHandler",)

INSTALLED_APPS += [  # noqa F405
    "django_extensions",
    "pattern_library",
    "dw_pattern_library",
]

if DEBUG:  # noqa F405
    X_FRAME_OPTIONS = "SAMEORIGIN"

TEMPLATES[0]["OPTIONS"]["builtins"] = ["pattern_library.loader_tags"]  # noqa F405

PATTERN_LIBRARY = {
    # Groups of templates for the pattern library navigation. The keys
    # are the group titles and the values are lists of template name prefixes that will
    # be searched to populate the groups.
    "SECTIONS": (
        ("dwds-extendable-elements", ["dwds/elements/extendable"]),
        ("dwds-components", ["dwds/components"]),
        ("dwds-layouts", ["dwds/layouts"]),
    ),
    # Configure which files to detect as templates.
    "TEMPLATE_SUFFIX": ".html",
    # # Set which template components should be rendered inside of,
    # # so they may use page-level component dependencies like CSS.
    "PATTERN_BASE_TEMPLATE_NAME": "pattern-library-base.html",
    # # Any template in BASE_TEMPLATE_NAMES or any template that extends a template in
    # # BASE_TEMPLATE_NAMES is a "page" and will be rendered as-is without being wrapped.
    "BASE_TEMPLATE_NAMES": ["base.html"],
}

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
