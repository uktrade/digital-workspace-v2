from .prod import *  # noqa F403

INSTALLED_APPS += [  # noqa F405
    "elasticapm.contrib.django",
]

ELASTIC_APM = {
    "SERVICE_NAME": "Digital Workspace",
    "SECRET_TOKEN": env("ELASTIC_APM_SECRET_TOKEN"),  # noqa F405
    "SERVER_URL": env("ELASTIC_APM_SERVER_URL"),  # noqa F405
    "ENVIRONMENT": env("APP_ENV"),  # noqa F405
    "SERVER_TIMEOUT": env("ELASTIC_APM_SERVER_TIMEOUT", default="20s"),  # noqa F405
}
