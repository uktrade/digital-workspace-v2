import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
import environ
import sentry_sdk
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot
from django.urls import reverse_lazy
from django_log_formatter_asim import ASIMFormatter
from django_log_formatter_ecs import ECSFormatter
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration


# Set directories to be used across settings
BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT_DIR = BASE_DIR.parent

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()

# Set required configuration from environment
# Should be one of the following: "local", "test", "dev", "staging", "training", "prod", "build"
APP_ENV = env.str("APP_ENV", "local")
GIT_COMMIT = env.str("GIT_COMMIT", None)

AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")

WAGTAILADMIN_BASE_URL = env("WAGTAIL_BASE_URL")

DEBUG = env.bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")

AUTH_USER_MODEL = "user.User"

# AWS
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env("AWS_REGION")
AWS_S3_REGION_NAME = env("AWS_REGION", default="eu-west-2")

# Asset path used in parser
NEW_ASSET_PATH = env("NEW_ASSET_PATH")

FILE_UPLOAD_HANDLERS = (
    "django_chunk_upload_handlers.clam_av.ClamAVFileUploadHandler",
    "django_chunk_upload_handlers.s3.S3FileUploadHandler",
)  # Order is important

# Storage
# https://docs.djangoproject.com/en/4.2/ref/settings/#storages

STORAGES = {
    "default": {
        # BACKEND must be set to 'storages.backends.s3boto3.S3Boto3Storage'
        # or a class than inherits from it if using S3FileUploadHandler for
        # file upload handling
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    # WhiteNoise
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

AWS_S3_FILE_OVERWRITE = False

CLEAN_FILE_NAME = True

# Celery file upload config
IGNORE_ANTI_VIRUS = env.bool("IGNORE_ANTI_VIRUS", False)

# Set optional configuration from environment
if env.str("DJANGO_EMAIL_BACKEND", None):
    EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")

# Sentry
SENTRY_DSN = env.str("SENTRY_DSN", None)
SENTRY_BROWSER_TRACES_SAMPLE_RATE = env.float("SENTRY_BROWSER_TRACES_SAMPLE_RATE", 0.0)


def filter_transactions(event, hint):
    url_string = event["request"]["url"]
    parsed_url = urlparse(url_string)

    if parsed_url.path.startswith("/pingdom"):
        return None

    return event


# Configure Sentry if a DSN is set
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=APP_ENV,
        release=GIT_COMMIT,
        integrations=[DjangoIntegration(), RedisIntegration()],
        send_default_pii=True,  # Enable associating exceptions to users
        enable_tracing=env.bool("SENTRY_ENABLE_TRACING", False),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", 0.0),
        before_send_transaction=filter_transactions,
    )

# Allow all hosts
# (this application will always be run behind a PaaS router or locally)
ALLOWED_HOSTS = setup_allowed_hosts(["*"])

# Set up Django
LOCAL_APPS = [
    "patch",
    "core.apps.CoreConfig",
    "feedback",
    "home",
    "content",
    "news",
    "working_at_dit",
    "tools",
    "about_us",
    "networks",
    "country_fact_sheet",
    "events",
    "dw_design_system",
    "dev_tools",
    "user.apps.UserConfig",
    "pingdom.apps.PingdomConfig",
    "peoplefinder.apps.PeoplefinderConfig",
    "countries.apps.CountriesConfig",
    "interactions.apps.InteractionsConfig",
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
    "generic_chooser",
    "waffle",
    "wagtailorderable",
    "django_cotton",
]

WAGTAIL_APPS = [
    "modelcluster",
    "taggit",
    "wagtail.contrib.settings",
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
    "wagtail_modeladmin",
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
        # Search apps must be last because it depends on models being loaded into memory
        "search",
        "extended_search",
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
    "waffle.middleware.WaffleMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [
            PROJECT_ROOT_DIR / "src" / "dw_design_system",
        ],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtailmenus.context_processors.wagtailmenus",
                "django_settings_export.settings_export",
                "core.context_processors.global_context",
            ],
            "libraries": {
                "workspace_navigation": "core.templatetags.workspace_navigation",
            },
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

if is_copilot():
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url_from_env("DATABASE_CREDENTIALS")
        )
    }
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASES = {
        "default": env.db(),
    }

INGESTED_MODELS_DATABASES = []

if "UK_STAFF_LOCATIONS_DATABASE_URL" in env:
    DATABASES["uk_staff_locations"] = env.db("UK_STAFF_LOCATIONS_DATABASE_URL")
    INGESTED_MODELS_DATABASES.append("uk_staff_locations")

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
    (
        "dwds",
        os.path.join(PROJECT_ROOT_DIR, "src", "dw_design_system", "dwds"),
    ),
]

STATIC_ROOT = os.path.join(PROJECT_ROOT_DIR, "static")
STATIC_URL = "/static/"

# TODO - investigate media config
MEDIA_ROOT = os.path.join(PROJECT_ROOT_DIR, "media")
MEDIA_URL = "https://static.workspace.trade.gov.uk/wp-content/"

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": not DEBUG,
        "STATS_FILE": os.path.join(PROJECT_ROOT_DIR, "webpack-stats.json"),
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    }
}

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

OPENSEARCH_URL = env("OPENSEARCH_URL")

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": OPENSEARCH_URL,
    },
}

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "extended_search.backends.backend.CustomSearchBackend",
        "AUTO_UPDATE": True,
        "ATOMIC_REBUILD": True,
        "URLS": [OPENSEARCH_URL],
        "INDEX": "wagtail",
        "TIMEOUT": 60,
        "OPTIONS": {},
        "INDEX_SETTINGS": {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                },
                "analysis": {
                    "filter": {
                        "english_snowball": {
                            "type": "snowball",
                            "language": "english",
                        },
                        "remove_spaces": {
                            "type": "pattern_replace",
                            "pattern": "[ ()+]",
                            "replacement": "",
                        },
                    },
                    "analyzer": {
                        "snowball": {
                            "tokenizer": "standard",
                            "filter": [
                                "english_snowball",
                                "stop",
                                "lowercase",
                                "asciifolding",
                            ],
                        },
                        # Used for keyword fields like acronyms and phone
                        # numbers - use with caution (it removes whitespace and
                        # tokenizes everything else into a single token)
                        "no_spaces": {
                            "tokenizer": "keyword",
                            "filter": "remove_spaces",
                        },
                    },
                },
            }
        },
    }
}

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

# ClamAV
CLAM_AV_USERNAME = env("CLAM_AV_USERNAME", default=None)
CLAM_AV_PASSWORD = env("CLAM_AV_PASSWORD", default=None)
CLAM_AV_DOMAIN = env("CLAM_AV_DOMAIN", default=None)

# Redis
if is_copilot():
    CELERY_BROKER_URL = (
        env("CELERY_BROKER_URL", default=None) + "?ssl_cert_reqs=required"
    )
else:
    CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=None)

# Celery
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CELERY_BROKER_URL,
        # "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "wp_",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# Google Tag Manager
GTM_CODE = env("GTM_CODE", default=None)
GTM_AUTH = env("GTM_AUTH", default=None)

# Perm secretary name
PERM_SEC_NAME = env("PERM_SEC_NAME", default=None)

# Using https://pypi.org/project/django-settings-export/ for template settings access
SETTINGS_EXPORT = [
    "DEBUG",
    "GTM_CODE",
    "GTM_AUTH",
    "PERM_SEC_NAME",
    "LEAVING_SERVICE_URL",
    "GIT_COMMIT",
    "APP_ENV",
    "SENTRY_DSN",
    "SENTRY_BROWSER_TRACES_SAMPLE_RATE",
    "SERVICE_CONTACT_EMAIL",
    "USE_SVG_LOGO",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "asim_formatter": {
            "()": ASIMFormatter,
        },
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "ecs": {
            "class": "logging.StreamHandler",
            "formatter": "ecs_formatter",
        },
        "simple": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
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
                "ecs",
                "simple",
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
                "ecs",
                "simple",
                "stdout",
            ],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "ecs",
                "simple",
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

if is_copilot():
    LOGGING["handlers"]["ecs"]["formatter"] = "asim_formatter"

DLFA_INCLUDE_RAW_LOG = True

# Django Tasks
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
        "ENQUEUE_ON_COMMIT": False,
    }
}

# Remove SSO protection from health check and Hawk authed URLs
AUTHBROKER_ANONYMOUS_PATHS = (
    "/ical/all/",
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

AUTHBROKER_INTROSPECTION_TOKEN = env("AUTHBROKER_INTROSPECTION_TOKEN", default="XXX")

# There are some big pages with lots of content that need to send many fields.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# Set file uploads to throw exception when virus found
CHUNK_UPLOADER_RAISE_EXCEPTION_ON_VIRUS_FOUND = True

# Set username field to be used in audit log as that's where store SSO email id
AUDIT_LOG_USER_FIELD = "username"

# Support request email and GOV.UK Notify details
SUPPORT_REQUEST_EMAIL = env("SUPPORT_REQUEST_EMAIL")
GOVUK_NOTIFY_API_KEY = env("GOVUK_NOTIFY_API_KEY")
PAGE_PROBLEM_EMAIL_TEMPLATE_ID = env("PAGE_PROBLEM_EMAIL_TEMPLATE_ID")

# Profile left DIT
PROFILE_DELETION_REQUEST_EMAIL = env("PROFILE_DELETION_REQUEST_EMAIL")
PROFILE_DELETION_REQUEST_EMAIL_TEMPLATE_ID = env(
    "PROFILE_DELETION_REQUEST_EMAIL_TEMPLATE_ID"
)

# Profile edited
PROFILE_EDITED_EMAIL_TEMPLATE_ID = env("PROFILE_EDITED_EMAIL_TEMPLATE_ID")

# Profile deleted
PROFILE_DELETED_EMAIL_TEMPLATE_ID = env("PROFILE_DELETED_EMAIL_TEMPLATE_ID")

#  Simple history prevent revert
SIMPLE_HISTORY_REVERT_DISABLED = True

# Set a custom user edit form in Wagtail admin
WAGTAIL_USER_EDIT_FORM = "core.forms.WagtailUserEditForm"

# Hawk authentication
DJANGO_HAWK = {
    "HAWK_INCOMING_ACCESS_KEY": env("HAWK_INCOMING_ACCESS_KEY"),
    "HAWK_INCOMING_SECRET_KEY": env("HAWK_INCOMING_SECRET_KEY"),
}

# Data workspace page sizes
PAGINATION_PAGE_SIZE = env.int("PAGINATION_PAGE_SIZE", 100)
PAGINATION_MAX_PAGE_SIZE = env.int("PAGINATION_MAX_PAGE_SIZE", 100)

# Home page
HIDE_NEWS = env.bool("HIDE_NEWS", False)

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Feedback notifications email
FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID = env("FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID")
FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS = env.list(
    "FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS", default=[]
)

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
        "hr-v1": {
            "model": "feedback.models.HRFeedback",
            "form": "feedback.forms.HRFeedbackForm",
            "view": "feedback.views.HRFeedbackFormView",
            "copy": {
                "SUBMIT_TITLE": None,
            },
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
USE_SVG_LOGO = True

SERVICE_CONTACT_EMAIL = env("SERVICE_CONTACT_EMAIL", default=None)

# Leaving Service
LEAVING_SERVICE_URL = env("LEAVING_SERVICE_URL", default=None)

# django-waffle
# https://waffle.readthedocs.io/en/stable/starting/configuring.html
WAFFLE_FLAG_MODEL = "core.FeatureFlag"
CACHE_FLAGS_IN_SESSION = True


# Search

# Bad search score multipliers
BAD_SEARCH_SCORE_MULTIPLIERS = {
    "all_pages": env.int("ALL_PAGES_BAD_SEARCH_SCORE_MULTIPLIER", 1),
    "people": env.int("PEOPLE_BAD_SEARCH_SCORE_MULTIPLIER", 1),
    "teams": env.int("TEAMS_BAD_SEARCH_SCORE_MULTIPLIER", 1),
}

# Cut-off value for lots/few search results
CUTOFF_SEARCH_RESULTS_VALUE = env.int("CUTOFF_SEARCH_RESULTS_VALUE", 20)

# Profiles made inactive within this number of days will be shown in search results to
# all users.
SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS = env.int(
    "SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS", 90
)

# Enable the caching of the generated search query DSLs
SEARCH_ENABLE_QUERY_CACHE = env.bool("SEARCH_ENABLE_QUERY_CACHE", True)

# Content Security Policy header settings
CSP_DEFAULT_SRC = ("'none'",)
CSP_SCRIPT_SRC = ("'none'",)
CSP_SCRIPT_SRC_ATTR = ("'none'",)
CSP_SCRIPT_SRC_ELEM = ("'none'",)
CSP_IMG_SRC = ("'none'",)
CSP_MEDIA_SRC = ("'none'",)
CSP_FRAME_SRC = ("'none'",)
CSP_FONT_SRC = ("'none'",)
CSP_CONNECT_SRC = ("'none'",)

CSP_REPORT_ONLY = True
CSP_REPORT_URI = env("CSP_REPORT_URI", default=None)

# Interactions
INACTIVE_REACTION_TYPES = env.list("INACTIVE_REACTION_TYPES", default=["unhappy"])

# Page auto deletion cutoffs
PAGE_AUTODELETION_PRE_NOTIFICATION_CUTOFF = env.int(
    "PAGE_AUTODELETION_PRE_NOTIFICATION_CUTOFF", 365
)
PAGE_AUTODELETION_POST_NOTIFICATION_CUTOFF = env.int(
    "PAGE_AUTODELETION_POST_NOTIFICATION_CUTOFF", 30
)
