from .base import *  # noqa

SECRET_KEY = "value-does-not-matter-for-build"

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": "value-does-not-matter-for-build",
    },
}

CLAM_AV_USERNAME = "value-does-not-matter-for-build"
CLAM_AV_PASSWORD = "value-does-not-matter-for-build"
CLAM_AV_DOMAIN = "value-does-not-matter-for-build"

APP_ENV = "value-does-not-matter-for-build"

DATABASES = {
    "default": {
        "username": "value-does-not-matter-for-build",
        "password": "value-does-not-matter-for-build",
        "dbname": "value-does-not-matter-for-build",
        "engine": "postgres",
        "port": 5432,
        "host": "localhost"
    }
}
