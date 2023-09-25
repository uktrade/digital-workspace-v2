import dj_database_url
import environ
import sentry_sdk
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.utility import is_copilot
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(PROJECT_ROOT_DIR, ".env")  # noqa F405
if os.path.exists(env_file):  # noqa F405
    env.read_env(env_file)
env.read_env()

# Set required configuration from environment
# Should be one of the following: "local", "test", "dev", "staging", "training", "prod"
APP_ENV = env.str("APP_ENV", "local")
GIT_COMMIT = env.str("GIT_COMMIT", None)

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

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

AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
AUTHBROKER_INTROSPECTION_TOKEN = env("AUTHBROKER_INTROSPECTION_TOKEN", default="XXX")

WAGTAILADMIN_BASE_URL = env("WAGTAIL_BASE_URL")

DEBUG = env.bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")

# Asset path used in parser
NEW_ASSET_PATH = env("NEW_ASSET_PATH")

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

if is_copilot():
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url_from_env("DATABASE_CREDENTIALS")
        )
    }
else:
    if "postgres" in VCAP_SERVICES:
        DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
    else:
        DATABASE_URL = os.getenv("DATABASE_URL")  # noqa F405

    DATABASES = {
        "default": env.db(),
    }

if "UK_STAFF_LOCATIONS_DATABASE_URL" in env:
    DATABASES["uk_staff_locations"] = env.db("UK_STAFF_LOCATIONS_DATABASE_URL")

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": not DEBUG,
        "STATS_FILE": os.path.join(PROJECT_ROOT_DIR, "webpack-stats.json"),  # noqa F405
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    }
}

if "opensearch" in VCAP_SERVICES:
    OPENSEARCH_URL = VCAP_SERVICES["opensearch"][0]["credentials"]["uri"]
else:
    OPENSEARCH_URL = env("OPENSEARCH_URL")

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": OPENSEARCH_URL,
    },
}

WAGTAILSEARCH_BACKENDS["default"]["URLS"] = [OPENSEARCH_URL]  # noqa F405

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

# Feedback notifications email
FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID = env("FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID")
FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS = env.list(
    "FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS", default=[]
)
