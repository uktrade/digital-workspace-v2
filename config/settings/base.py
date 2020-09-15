import os
from base64 import b64decode
import environ

import sentry_sdk
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration

# Set directories to be used across settings
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)

VCAP_SERVICES = env.json('VCAP_SERVICES', {})

# Set required configuration from environment
APP_ENV = env.str("APP_ENV", "local")
AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
BASE_URL = env("WAGTAIL_BASE_URL")
DEBUG = env.bool("DJANGO_DEBUG", False)
PEOPLEFINDER_PROFILE_API_PRIVATE_KEY = b64decode(env("PEOPLEFINDER_PROFILE_API_PRIVATE_KEY"), validate=True)
PEOPLEFINDER_PROFILE_API_URL = env("PEOPLEFINDER_PROFILE_API_URL")
PEOPLEFINDER_URL = env("PEOPLEFINDER_URL")
SECRET_KEY = env("DJANGO_SECRET_KEY")

# AWS
if 'aws-s3-bucket' in VCAP_SERVICES:
    app_bucket_creds = VCAP_SERVICES['aws-s3-bucket'][0]['credentials']
    AWS_ACCESS_KEY_ID = app_bucket_creds["aws_access_key_id"]
    AWS_SECRET_ACCESS_KEY = app_bucket_creds["aws_secret_access_key"]
    AWS_REGION = app_bucket_creds["aws_region"]
    AWS_S3_REGION_NAME = app_bucket_creds["aws_region"]
    AWS_STORAGE_BUCKET_NAME = app_bucket_creds["bucket_name"]
else:
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = env("AWS_REGION")
    AWS_S3_REGION_NAME =env("AWS_REGION")

# Legacy bucket
LEGACY_AWS_STORAGE_BUCKET_NAME = env("LEGACY_AWS_STORAGE_BUCKET_NAME")
LEGACY_AWS_ACCESS_KEY_ID = env("LEGACY_AWS_ACCESS_KEY_ID")
LEGACY_AWS_SECRET_ACCESS_KEY = env("LEGACY_AWS_SECRET_ACCESS_KEY")

# Set optional configuration from environment
if env.str("DJANGO_EMAIL_BACKEND", None):
    EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")


# Configure Sentry if a DSN is set
if env.str("SENTRY_DSN", None):
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        environment=APP_ENV,
        integrations=[DjangoIntegration()],
        send_default_pii=True  # Enable associating exceptions to users
    )


# Configure Django security settings unless running locally
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 15768000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True


# Configure logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "DEBUG" if DEBUG else "WARNING",
        "handlers": ["console"]
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose"
        }
    }
}


# Allow all hosts
# (this application will always be run behind a PaaS router or locally)
ALLOWED_HOSTS = ["*"]


# Set up Django
LOCAL_APPS = [
    "core",
    "home",
    "content",
    "search",
    "news",
    "working_at_dit",
    "tools",
    "about_us",
    "transition",
    "networks",
    "import_wordpress",
]

THIRD_PARTY_APPS = [
    "authbroker_client",
    "webpack_loader",
    "storages",
]

WAGTAIL_APPS = [
    "wagtail.contrib.forms",
    "wagtail.contrib.postgres_search",
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
    "wagtail.core",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.modeladmin",

    "modelcluster",
    "taggit",
    "wagtailmedia",
    "wagtailmenus",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles"
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

    "wagtail.core.middleware.SiteMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",

    #"authbroker_client.middleware.ProtectAllViewsMiddleware",  # TODO - restore
    "core.middleware.GetPeoplefinderProfileMiddleware",
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
            ],
            "libraries": {
                "workspace_navigation": "core.templatetags.workspace_navigation",
            }
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

if 'postgres' in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES['postgres'][0]['credentials']['uri']
else:
    DATABASE_URL = os.getenv('DATABASE_URL')

DATABASES = {"default": env.db()}


# Configure authentication and Staff SSO integration
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend"
]

LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = "/"


# Configure date/time format (GDS style)
DATE_FORMAT = "j F Y"
TIME_FORMAT = "P"
DATETIME_FORMAT = r"j F Y \a\t P"


# Configure assets
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder"
]

STATICFILES_DIRS = [
    #os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "assets")
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


# Configure Wagtail
WAGTAIL_SITE_NAME = "workspace"

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.contrib.postgres_search.backend"
    }
}

CAN_ELEVATE_SSO_USER_PERMISSIONS = False

WAGTAILMENUS_ACTIVE_CLASS = "govuk-header__navigation-item--active--ws"

NAMESPACES = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}

synonyms = []
stop_words = []

synonyms_file = os.path.join(
    BASE_DIR, 'config/synonyms.txt'
)

stop_words_file = os.path.join(
    BASE_DIR, 'config/stop-words.txt'
)

with open(synonyms_file) as synonyms_file:
    for line in synonyms_file:
        # TODO - handle "=>"
        if line.strip().startswith('#'):
            continue
        synonyms.append(line.strip())

with open(stop_words_file) as stop_words_file:
    for line in stop_words_file:
        if line.strip().startswith('#'):
            continue
        stop_words.append(line.strip())

if 'elasticsearch' in VCAP_SERVICES:
    ELASTIC_SEARCH_URL = VCAP_SERVICES['elasticsearch'][0]["credentials"]["uri"]
else:
    ELASTIC_SEARCH_URL = env("ELASTIC_SEARCH_URL")

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.elasticsearch7',
        'URLS': [ELASTIC_SEARCH_URL,],
        'INDEX': 'wagtail',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                },
                "analysis": {
                    "analyzer": {
                        "default": {
                            "tokenizer": "lowercase",
                            "filter": [
                                "lowercase",
                                "search_stop_words",
                                "search_synonyms",
                                #"search_snowball",
                            ]
                        },
                        # Override edgengram_analyzer to remove unwanted "asciifolding" and "edgengram" filters
                        "edgengram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": [
                                "lowercase",
                                "search_stop_words",
                                "search_synonyms",
                            ]
                        },
                        # Override edgengram_analyzer to remove unwanted filters
                        "ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": [
                                "lowercase",
                                "search_stop_words",
                                "search_synonyms",
                            ]
                        },
                    },
                    "filter": {
                        "search_stop_words": {
                            "type": "stop",
                            "stopwords": stop_words
                        },
                        "search_synonyms": {
                            "type": "synonym",
                            "lenient": True,
                            "synonyms": synonyms
                        },
                        # "search_snowball": {
                        #     "type": "snowball",
                        #     "language": "English"
                        # }
                    },
                    # "tokenizer": {
                    #     "search_tokenizer": {
                    #         "type": "ngram",
                    #         "min_gram": 3,
                    #         "max_gram": 3,
                    #         "token_chars": [
                    #             "letter",
                    #             "digit"
                    #         ]
                    #     }
                    # },
                }
            }
        }
    }
}
