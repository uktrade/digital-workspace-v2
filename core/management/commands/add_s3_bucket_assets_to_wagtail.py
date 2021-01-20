import io
import boto3
import os
import sys
from datetime import datetime


from PIL.Image import frombytes

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

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

embed_sql = """
INSERT INTO public.wagtailembeds_embed(
	id, url, max_width, type, html, title, author_name, provider_name, thumbnail_url, width, height, last_updated)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

document_sql = """
INSERT INTO public.wagtaildocs_document(
	title, file, created_at, uploaded_by_user_id, collection_id, file_size, file_hash)
	VALUES ({1}, {2}, {3}, {3}, 1, {4}, {5});
"""

IMG_SQL_TEMPLATE = """
INSERT INTO public.wagtailimages_image(
	title, file, width, height, created_at, uploaded_by_user_id, file_size, collection_id, file_hash)
	VALUES ({1}, {2}, {3}, {4}, {5}, {6}, {7}, 1, {8});
"""

media_sql = """
INSERT INTO public.wagtailmedia_media(
	title, file, type, duration, width, height, thumbnail, created_at, collection_id, uploaded_by_user_id)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

User = get_user_model()


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            user = User.objects.filter(username="admin")

            session = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_ACCESS_KEY_ID,
            )

            s3 = session.resource('s3')

            asset_bucket = s3.Bucket(
                settings.AWS_STORAGE_BUCKET_NAME,
            )

            for asset_key in asset_bucket.objects.all():
                s3_response_object = s3.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=asset_key,
                )

                s3_bytes = s3_response_object['Body'].read()
                asset_bytes = io.BytesIO(s3_bytes)
                file_name = os.path.basename(asset_key)

                if asset_key.endswith(IMG_EXTENSIONS):
                    img = frombytes(asset_bytes)
                    image_sql = IMG_SQL_TEMPLATE.format(
                        file_name,
                        asset_key,
                        img.width,
                        img.height,
                        datetime.now(),
                        user.id,
                        sys.getsizeof(asset_bytes),
                        1,
                        hash(asset_bytes),
                    )
                    cursor.execute(image_sql)
