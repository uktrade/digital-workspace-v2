from .base import *  # noqa

CAN_ELEVATE_SSO_USER_PERMISSIONS = True

# Set to True if you need to upload documents and you are not running
# the ClamAV service locally.
SKIP_CLAM_AV_FILE_UPLOAD = False

if SKIP_CLAM_AV_FILE_UPLOAD:
    FILE_UPLOAD_HANDLERS = (
        # "file_upload_handler.clam_av.ClamAVFileUploadHandler",
        "file_upload_handler.s3.S3FileUploadHandler",
    )  # Order is important
