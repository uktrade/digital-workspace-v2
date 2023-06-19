import os
import sys

import environ
import sentry_sdk
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration


# Set directories to be used across settings
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(PROJECT_ROOT_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)
env.read_env()

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

# Set required configuration from environment
# Should be one of the following: "local", "test", "dev", "staging", "training", "prod"
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
if "aws-s3-bucket" in VCAP_SERVICES:
    app_bucket_creds = VCAP_SERVICES["aws-s3-bucket"][0]["credentials"]
    AWS_REGION = app_bucket_creds["aws_region"]
    AWS_S3_REGION_NAME = app_bucket_creds["aws_region"]
    AWS_STORAGE_BUCKET_NAME = app_bucket_creds["bucket_name"]
else:
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_REGION = env("AWS_REGION")
    AWS_S3_REGION_NAME = env("AWS_REGION", default="eu-west-2")

# You don't seem to be able to sign S3 URLs with VCAP S3 creds
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_S3_HOST = "s3-eu-west-2.amazonaws.com"

# Asset path used in parser
NEW_ASSET_PATH = env("NEW_ASSET_PATH")

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

# Celery file upload config
IGNORE_ANTI_VIRUS = env.bool("IGNORE_ANTI_VIRUS", False)

# Set optional configuration from environment
if env.str("DJANGO_EMAIL_BACKEND", None):
    EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")

# Configure Sentry if a DSN is set
if env.str("SENTRY_DSN", None):
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        environment=APP_ENV,
        release=GIT_COMMIT,
        integrations=[DjangoIntegration(), RedisIntegration()],
        send_default_pii=True,  # Enable associating exceptions to users
    )

# Allow all hosts
# (this application will always be run behind a PaaS router or locally)
ALLOWED_HOSTS = ["*"]

# Set up Django
LOCAL_APPS = [
    "core",
    "home",
    "content",
    "search_extended",
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

INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + WAGTAIL_APPS + DJANGO_APPS

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

if "postgres" in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

DATABASES = {"default": env.db()}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Configure authentication and Staff SSO integration
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.backends.CustomAuthbrokerBackend",
]

LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = "/"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
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

if "opensearch" in VCAP_SERVICES:
    OPENSEARCH_URL = VCAP_SERVICES["opensearch"][0]["credentials"]["uri"]
else:
    OPENSEARCH_URL = env("OPENSEARCH_URL")

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": OPENSEARCH_URL,
    },
}

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "search_extended.backends.backend.CustomSearchBackend",
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
                            "language": "English"
                        },
                    },
                    "analyzer": {
                        "snowball": {
                            "tokenizer": "standard",
                            "filter": [
                                "english_snowball",
                            ],
                        },
                        # "no_spaces": {
                        #     "type": "pattern",
                        #     "pattern": "",
                        #     "lowercase": True
                        # }
                    },
                },
            }
        },
    }
}

SEARCH_EXTENDED = {
    "BOOST_VARIABLES": {
        "PAGE_TITLE": 5.0,
        "PAGE_HEADINGS": 3.0,
        "PAGE_EXCERPT": 2.0,
        "PAGE_CONTENT": 1.0,
        "PAGE_TOOLS_PHRASE_TITLE_EXPLICIT": 2.0,
        "PAGE_GUIDANCE_PHRASE_TITLE_EXPLICIT": 2.0,
        "PERSON_NAME": 4.0,
        "PERSON_EMAIL_PHONE": 4.0,
        "PERSON_ROLE": 3.0,
        "PERSON_TEAM": 2.0,
        "PERSON_LOCATION": 1.5,
        "PERSON_SKILLS": 1.5,
        "PERSON_LANGUAGES": 1.5,
        "PERSON_NETWORKS": 1.5,
        "PERSON_ADDITIONAL_ROLES": 0.8,
        "PERSON_INTERESTS": 0.8,
        "PERSON_PROFILE_COMPLETENESS": 2.0,
        "PERSON_HAS_PHOTO": 1.5,
        "TEAM_NAME": 4.0,
        "TEAM_ABBREVIATION": 5.0,
        "TEAM_DESCRIPTION": 3.0,
        "TEAM_ROLES": 2.0,
        "SEARCH_PHRASE": 10.0,
        "SEARCH_QUERY_AND": 2.5,
        "SEARCH_QUERY_OR": 1.0,
        "ANALYZER_EXPLICIT": 3.5,
        "ANALYZER_TOKENIZED": 1.0,
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
if "redis" in VCAP_SERVICES:
    credentials = VCAP_SERVICES["redis"][0]["credentials"]
    CELERY_BROKER_URL = "rediss://:{0}@{1}:{2}/0?ssl_cert_reqs=required".format(
        credentials["password"],
        credentials["host"],
        credentials["port"],
    )
else:
    CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=None)

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

# Twitter
TWITTER_ACCESS_TOKEN = env("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = env("TWITTER_ACCESS_SECRET")

TWITTER_OAUTH_CONSUMER_KEY = env("TWITTER_OAUTH_CONSUMER_KEY")
TWITTER_OAUTH_CONSUMER_SECRET = env("TWITTER_OAUTH_CONSUMER_SECRET")

TWITTER_DEPT_USER = env("TWITTER_DEPT_USER")
TWITTER_PERM_SEC_USER = env("TWITTER_PERM_SEC_USER", default=None)

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
            "level": "DEBUG",
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
)

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

# Person update web hook
PERSON_UPDATE_HAWK_ID = env("PERSON_UPDATE_HAWK_ID", None)
PERSON_UPDATE_HAWK_KEY = env("PERSON_UPDATE_HAWK_KEY", None)
PERSON_UPDATE_WEBHOOK_URL = env("PERSON_UPDATE_WEBHOOK_URL", None)

# Home page
HIDE_NEWS = env.bool("HIDE_NEWS", False)

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["gds"]
CRISPY_TEMPLATE_PACK = "gds"

# Feedback
DJANGO_FEEDBACK_GOVUK = {
    "SERVICE_NAME": "the beta experience",
    "FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID": env(
        "FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID"
    ),
    "FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS": env.list(
        "FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS", default=[]
    ),
    "COPY": {
        "SUBMIT_TITLE": "Give your feedback on the beta search experience",
        "FIELD_SATISFACTION_LEGEND": "How do you feel about your search experience today?",
        "FIELD_COMMENT_LEGEND": "Tell us why you gave that rating",
        "FIELD_COMMENT_HINT": "If you do not want to be contacted about more research opportunities, you can let us know here.",
    },
}
