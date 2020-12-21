import io
import boto3
import os

from django.conf import settings
from django.core.files.images import ImageFile

from django.core.files.images import ImageFile


from wagtail.documents.models import Document
from wagtail.embeds.models import Embed


IMG_EXTENSIONS = (
    ".jpg",
    ".png",
    ".webp",
    ".gif",
    ".apng",
    ".avif",
    ".jpeg",
    ".svg",
)

VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
)


def process_bucket():
    session = boto3.Session(
        aws_access_key_id=settings.LEGACY_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.LEGACY_AWS_SECRET_ACCESS_KEY,
    )

    s3 = session.resource('s3')

    asset_bucket = s3.Bucket(
        settings.LEGACY_AWS_STORAGE_BUCKET_NAME,
    )

    for asset_key in asset_bucket.objects.all():
        if not asset_key.endswith(IMG_EXTENSIONS):
            s3_response_object = s3.get_object(
                Bucket=settings.LEGACY_AWS_STORAGE_BUCKET_NAME,
                Key=asset_key,
            )

            s3_bytes = s3_response_object['Body'].read()

            asset_bytes = io.BytesIO(s3_bytes)
            file_name = os.path.basename(asset_key)

            if asset_key.endswith(VIDEO_EXTENSIONS):
                # Video
                pass
            else:



