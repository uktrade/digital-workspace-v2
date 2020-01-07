"""Django settings for the Digital Workspace project."""

import os

import environ
from django.urls import reverse_lazy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(BASE_DIR, "core")

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)

AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
BASE_URL = env("WAGTAIL_BASE_URL")
DEBUG = env.bool("DJANGO_DEBUG", False)
PEOPLEFINDER_API_KEY = env("PEOPLEFINDER_API_KEY")
PEOPLEFINDER_API_URL = env("PEOPLEFINDER_API_URL")
PEOPLEFINDER_URL = env("PEOPLEFINDER_URL")
SECRET_KEY = env("DJANGO_SECRET_KEY")

if env.str("DJANGO_EMAIL_BACKEND", None):
    EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")

# This application will always be run behind a PaaS router (or locally),
# so all hosts can be whitelisted
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "home",
    "content",
    "search",

    "authbroker_client",
    "webpack_loader",

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
    "wagtailmedia",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles"
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",

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

# Use Staff SSO for authentication
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend"
]
LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = "/"


# GDS style date/time format
DATE_FORMAT = "j F Y"
TIME_FORMAT = "P"
DATETIME_FORMAT = r"j F Y \a\t P"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder"
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
    os.path.join(BASE_DIR, "assets")
]

# ManifestStaticFilesStorage is recommended in production, to prevent outdated
# Javascript / CSS assets being served from cache (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/2.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


# Wagtail settings

WAGTAIL_SITE_NAME = "workspace"

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.contrib.postgres_search.backend"
    }
}
