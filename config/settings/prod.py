from .base import *  # noqa

MIDDLEWARE += [
    "authbroker_client.middleware.ProtectAllViewsMiddleware",
]

AWS_S3_HOST = "s3-eu-west-2.amazonaws.com"

# DEFAULT_FILE_STORAGE must be set to 'storages.backends.s3boto3.S3Boto3Storage'
# or a class than inherits from it if using S3FileUploadHandler for
# file upload handling
DEFAULT_FILE_STORAGE = "core.asset_storage.AssetStorage"

AWS_S3_URL_PROTOCOL = "https"
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")
#AWS_S3_CUSTOM_DOMAIN = "assets.workspace.trade.uat.uktrade.io"
AWS_QUERYSTRING_AUTH = True

# s3chunkuploader
FILE_UPLOAD_HANDLERS = (
    #'file_upload_handler.clam_av.ClamAVFileUploadHandler',
    'file_upload_handler.s3.S3FileUploadHandler',
)  # Order is important

#AWS_DEFAULT_ACL = None
#AWS_S3_SIGNATURE_VERSION = 's3v4'

# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = 'DENY'
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_HSTS_SECONDS = 15768000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
