import os
import sys

from dbt_copilot_python.network import setup_allowed_hosts
from django.urls import reverse_lazy

# Set directories to be used across settings
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

AUTH_USER_MODEL = "user.User"

# DEFAULT_FILE_STORAGE must be set to 'storages.backends.s3boto3.S3Boto3Storage'
# or a class than inherits from it if using S3FileUploadHandler for
# file upload handling
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

FILE_UPLOAD_HANDLERS = (
    "django_chunk_upload_handlers.clam_av.ClamAVFileUploadHandler",
    "django_chunk_upload_handlers.s3.S3FileUploadHandler",
)  # Order is important

AWS_S3_FILE_OVERWRITE = False

CLEAN_FILE_NAME = True

# Allow all hosts
# (this application will always be run behind a PaaS router or locally)
ALLOWED_HOSTS = setup_allowed_hosts(["*"])

# Set up Django
LOCAL_APPS = [
    "core",
    "feedback",
    "home",
    "content",
    "search",
    "news",
    "working_at_dit",
    "tools",
    "about_us",
    "transition",
    "networks",
    "country_fact_sheet",
    "user.apps.UserConfig",
    "pingdom.apps.PingdomConfig",
    "peoplefinder.apps.PeoplefinderConfig",
    "countries.apps.CountriesConfig",
]

THIRD_PARTY_APPS = [
    "authbroker_client",
    "webpack_loader",
    "storages",
    "django_elasticsearch_dsl",
    "simple_history",
    "django_chunk_upload_handlers",
    "django_audit_log_middleware",
    "rest_framework",
    "django_celery_beat",
    "crispy_forms",
    "crispy_forms_gds",
    "django_feedback_govuk",
]

WAGTAIL_APPS = [
    "modelcluster",
    "taggit",
    "wagtail.contrib.search_promotions",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.table_block",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.modeladmin",
    "wagtailmedia",
    "wagtailmenus",
    "wagtail_draftail_anchors",
    "wagtail_adminsortable",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
]

INSTALLED_APPS = (
    LOCAL_APPS
    + THIRD_PARTY_APPS
    + WAGTAIL_APPS
    + DJANGO_APPS
    + [
        "extended_search",  # must be last because it depends on models being loaded into memory
    ]
)

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "authbroker_client.middleware.ProtectAllViewsMiddleware",
    "core.middleware.GetPeoplefinderProfileMiddleware",
    "core.middleware.TimezoneMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django_audit_log_middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtailmenus.context_processors.wagtailmenus",
                "django_settings_export.settings_export",
                "core.context_processors.page_problem_form",
            ],
            "libraries": {
                "workspace_navigation": "core.templatetags.workspace_navigation",
            },
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_ROUTERS = ["peoplefinder.routers.IngestedModelsRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Configure authentication and Staff SSO integration
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.backends.CustomAuthbrokerBackend",
]

LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = "/"

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
LOCAL_TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# Configure date/time format (GDS style)
DATE_FORMAT = "j F Y"
TIME_FORMAT = "P"
DATETIME_FORMAT = r"j F Y \a\t P"

# Configure assets
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT_DIR, "assets"),
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

STATIC_ROOT = os.path.join(PROJECT_ROOT_DIR, "static")
STATIC_URL = "/static/"

# TODO - investigate media config
MEDIA_ROOT = os.path.join(PROJECT_ROOT_DIR, "media")
MEDIA_URL = "https://static.workspace.trade.gov.uk/wp-content/"

# Configure Wagtail
WAGTAIL_SITE_NAME = "Digital Workspace"

CAN_ELEVATE_SSO_USER_PERMISSIONS = False

WAGTAILMENUS_ACTIVE_CLASS = "govuk-header__navigation-item--active--ws"

synonyms = []
stop_words = []

synonyms_file = os.path.join(BASE_DIR, "config/synonyms.txt")
stop_words_file = os.path.join(BASE_DIR, "config/stop-words.txt")

with open(synonyms_file) as synonyms_file:
    for line in synonyms_file:
        # TODO - handle "=>"
        if line.strip().startswith("#"):
            continue
        synonyms.append(line.strip())

with open(stop_words_file) as stop_words_file:
    for line in stop_words_file:
        if line.strip().startswith("#"):
            continue
        stop_words.append(line.strip())

SEARCH_EXTENDED = {
    "boost_parts": {
        "extras": {
            "page_tools_phrase_title_explicit": 2.0,
            "page_guidance_phrase_title_explicit": 2.0,
        },
        "query_types": {
            "phrase": 20.5,
        },
    }
}

# Add a custom provider
# Your custom provider must support oEmbed for this to work. You should be
# able to find these details in the provider's documentation.
# - 'endpoint' is the URL of the oEmbed endpoint that Wagtail will call
# - 'urls' specifies which patterns
ms_stream_provider = {
    "endpoint": "https://web.microsoftstream.com/oembed",
    "urls": [
        "^https://.+?.microsoftstream.com/video/.+$",
    ],
}
# https://*.microsoftstream.com/video/ID
# https://web.microsoftstream.com/video/2db4eeae-f9f8-4324-997a-41f682dea240 /PS-IGNORE

# Need a custom youtube provider because the Wagtail default has a bug
youtube_provider = {
    "endpoint": "https://www.youtube.com/oembed",
    "urls": [
        "^https://www.youtube.com/watch.+$",
    ],
}

WAGTAILEMBEDS_FINDERS = [
    {
        "class": "wagtail.embeds.finders.oembed",
        "providers": [
            youtube_provider,
            ms_stream_provider,
        ],  # , vimeo, ms_stream_provider
    }
]

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Using https://pypi.org/project/django-settings-export/ for template settings access
SETTINGS_EXPORT = [
    "DEBUG",
    "GTM_CODE",
    "GTM_AUTH",
    "PERM_SEC_NAME",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "opensearch": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("OPENSEARCH_LOG_LEVEL", "INFO"),
        },
        "environ": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("ENVIRON_LOG_LEVEL", "INFO"),
        },
    },
}

# Remove SSO protection from health check and Hawk authed URLs
AUTHBROKER_ANONYMOUS_PATHS = (
    "/pingdom/ping.xml",
    "/peoplefinder/api/activity-stream/",
    "/peoplefinder/api/person-api/",
)
AUTHBROKER_ANONYMOUS_URL_NAMES = (
    "person-api-people-list",
    "person-api-people-detail",
    "team-api-teams-list",
    "profile-get-card",
)

# There are some big pages with lots of content that need to send many fields.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# Set file uploads to throw exception when virus found
CHUNK_UPLOADER_RAISE_EXCEPTION_ON_VIRUS_FOUND = True

# Set username field to be used in audit log as that's where store SSO email id
AUDIT_LOG_USER_FIELD = "username"

#  Simple history prevent revert
SIMPLE_HISTORY_REVERT_DISABLED = True

# Set a custom user edit form in Wagtail admin
WAGTAIL_USER_EDIT_FORM = "core.forms.WagtailUserEditForm"

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Feedback
DJANGO_FEEDBACK_GOVUK = {
    "SERVICE_NAME": "the beta experience",
    "COPY": {
        "SUBMIT_TITLE": "Providing feedback on your experience will help us improve the service",
        "FIELD_SATISFACTION_LEGEND": "How satisfied are you with Digital Workspace?",
        "FIELD_COMMENT_LEGEND": "How could we improve this service?",
        "FIELD_COMMENT_HINT": "If you do not want to be contacted about more research opportunities, you can let us know here.",
    },
    "FEEDBACK_FORMS": {
        "default": {
            "model": "django_feedback_govuk.models.Feedback",
            "form": "django_feedback_govuk.forms.FeedbackForm",
            "view": "django_feedback_govuk.views.FeedbackView",
        },
        "search-v1": {
            "model": "feedback.models.SearchFeedbackV1",
            "form": "feedback.forms.SearchFeedbackV1Form",
            "view": "django_feedback_govuk.views.FeedbackView",
        },
        "search-v2": {
            "model": "feedback.models.SearchFeedbackV2",
            "form": "feedback.forms.SearchFeedbackV2Form",
            "view": "feedback.views.SearchFeedbackV2FormView",
            "copy": {
                "SUBMIT_TITLE": None,
            },
        },
    },
}

VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING = "value-does-not-matter-for-build"

APP_ENV = "build"

SECRET_KEY = VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING,
    },
}

CLAM_AV_USERNAME = VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING
CLAM_AV_PASSWORD = VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING
CLAM_AV_DOMAIN = VALUE_DOES_NOT_MATTER_FOR_BUILD_STRING
