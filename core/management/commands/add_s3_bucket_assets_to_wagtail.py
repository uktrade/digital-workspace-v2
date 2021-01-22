import hashlib
import boto3
import os
from datetime import datetime

from PIL import Image
from io import BytesIO

from wagtail.images.models import Image as WagtailImage
from wagtail.core.models import Collection

from taggit.models import Tag

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
)

VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
)

DOCUMENT_SQL = """
INSERT INTO public.wagtaildocs_document(
    title, file, created_at, uploaded_by_user_id, collection_id, file_size, file_hash)
    VALUES (`{1}`, {2}, {3}, {3}, 1, {4}, {5});
"""

IMG_SQL_TEMPLATE = """
INSERT INTO public.wagtailimages_image(
    title, file, width, height, created_at, uploaded_by_user_id, file_size, collection_id, file_hash)
    VALUES ('{0}', '{1}', {2}, {3}, '{4}', {5}, {6}, {7}, '{8}');
"""

MEDIA_SQL = """
INSERT INTO public.wagtailmedia_media(
    title, file, type, duration, width, height, thumbnail, created_at, collection_id, uploaded_by_user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

User = get_user_model()


class ImageAlreadyExistsException(Exception):
    pass


class ErrorGettingYearMonthException(Exception):
    pass


def get_month_year(key):
    # wp-content/uploads/2021/01/
    try:
        parts = key.split("/")
        year = parts[2]
        month = datetime.date(1900, parts[3], 1).strftime('%B')
        return month, year,
    except:
        raise ErrorGettingYearMonthException()


def create_image_record(
    cursor,
    file_name,
    key,
    file_data,
    file_size,
    file_hash,
    user,
):
    # See if image already exists
    if WagtailImage.objects.filter(file=key).first():
        print("Image already exists in database, skipping")
        raise ImageAlreadyExistsException()

    year, month = get_month_year(key)

    collection = Collection.objects.filter(name=year).first()

    if not collection:
        root_collection = Collection.get_first_root_node()
        collection = root_collection.add_child(name=year)

    try:
        img = Image.open(BytesIO(file_data))
        image_sql = IMG_SQL_TEMPLATE.format(
            file_name,
            key,
            img.width,
            img.height,
            datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            user.id,
            file_size,
            collection.id,
            file_hash,
        )
        cursor.execute(image_sql)
    except Exception as ex:
        print("COULD NOT PROCESS IMAGE, ex: ", ex)

    # Create tags
    image = WagtailImage.objects.filter(
        file=key
    ).first()

    image.tags.add(month)


class Command(BaseCommand):
    help = "Generate database records for assets on S3"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            user = User.objects.filter(username="admin").first()

            session = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            s3 = session.resource('s3')

            asset_bucket = s3.Bucket(
                settings.AWS_STORAGE_BUCKET_NAME,
            )

            for bucket_object in asset_bucket.objects.all():
                print(f"Processing object {bucket_object.key}")
                obj = s3.Object(
                    settings.AWS_STORAGE_BUCKET_NAME,
                    bucket_object.key,
                )
                file_data = obj.get()['Body'].read()

                file_hash = hashlib.sha1(file_data).hexdigest()
                file_name = os.path.basename(bucket_object.key)

                if bucket_object.key.endswith(IMG_EXTENSIONS):
                    try:
                        create_image_record(
                            cursor,
                            file_name,
                            bucket_object.key,
                            file_data,
                            bucket_object.size,
                            file_hash,
                            user,
                        )
                    except ImageAlreadyExistsException:
                        continue
                    except ErrorGettingYearMonthException:
                        continue
