"""Django settings for the Digital Workspace project."""

import os

import environ
import sentry_sdk
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration


# Set directories to be used across settings
BASE_DIR = environ.Path(__file__) - 2  # The root directory of the project
PROJECT_DIR = os.path.join(BASE_DIR, "core")  # The project's "main" application


# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)


# Set required configuration from environment
APP_ENV = env.str("APP_ENV", "local")
AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
BASE_URL = env("WAGTAIL_BASE_URL")
DEBUG = env.bool("DJANGO_DEBUG", False)
PEOPLEFINDER_API_KEY = env("PEOPLEFINDER_API_KEY")
PEOPLEFINDER_API_URL = env("PEOPLEFINDER_API_URL")
PEOPLEFINDER_URL = env("PEOPLEFINDER_URL")
SECRET_KEY = env("DJANGO_SECRET_KEY")


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
        "level": "WARNING",
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
    "home",
    "content",
    "search"
]

THIRD_PARTY_APPS = [
    "authbroker_client",
    "webpack_loader"
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

    "modelcluster",
    "taggit",
    "wagtailmedia"
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

    "authbroker_client.middleware.ProtectAllViewsMiddleware",
    "core.middleware.GetPeoplefinderProfileMiddleware"
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages"
            ],
            "libraries": {
                "workspace_navigation": "core.templatetags.workspace_navigation"
            }
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

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
    os.path.join(PROJECT_DIR, "static"),
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
