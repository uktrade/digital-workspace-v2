from .base import *  # noqa
import logging
import requests

import sys

from django_log_formatter_ecs import ECSFormatter

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

LOG_TO_ELK = env.bool("LOG_TO_ELK", default=False)
ELK_ADDRESS = env("ELK_ADDRESS", default=None)

AWS_S3_HOST = "s3-eu-west-2.amazonaws.com"

# DEFAULT_FILE_STORAGE must be set to 'storages.backends.s3boto3.S3Boto3Storage'
# if using S3FileUploadHandler for file upload handling

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# AWS_S3_URL_PROTOCOL = "https"
# AWS_S3_CUSTOM_DOMAIN = "static.workspace.trade.gov.uk"
# AWS_QUERYSTRING_AUTH = False

# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# STATIC_ROOT = os.path.join(BASE_DIR, "static")
# STATIC_URL = "/static/"



# s3chunkuploader
FILE_UPLOAD_HANDLERS = (
    'file_upload_handler.clam_av.ClamAVFileUploadHandler',
    'file_upload_handler.s3.S3FileUploadHandler',
)  # Order is important

AV_SIGNATURE_SECRET_KEY = "secret key!!!"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "stdout": {"class": "logging.StreamHandler", "stream": sys.stdout, },
        "null": {"class": "logging.NullHandler", },
    },
    "root": {"handlers": ["stdout"], "level": os.getenv("ROOT_LOG_LEVEL", "INFO"), },
    "loggers": {
        "django": {
            "handlers": ["stdout", ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "django.server": {
            "handlers": ["stdout", ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}
