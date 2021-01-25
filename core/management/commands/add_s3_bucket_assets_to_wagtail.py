import hashlib
import boto3
import os
from datetime import datetime

from PIL import Image
from io import BytesIO

from wagtailmedia.models import Media as WagtailMedia

from wagtail.images.models import Image as WagtailImage
from wagtail.documents.models import Document as WagtailDocument
from wagtail.core.models import Collection

from taggit.models import Tag

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

DOCUMENT_EXTENSIONS = (
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".pdf",
)

IMG_EXTENSIONS = (
    ".jpg",
    ".png",
    ".webp",
    ".gif",
    ".apng",
    ".avif",
    ".jpeg",
)

MEDIA_EXTENSIONS = (
    ".mp4",
    ".mov",
)

DOCUMENT_SQL_TEMPLATE = """
INSERT INTO public.wagtaildocs_document(
    title, file, created_at, uploaded_by_user_id, collection_id, file_size, file_hash)
    VALUES (`{1}`, {2}, {3}, {3}, 1, {4}, {5});
"""

IMG_SQL_TEMPLATE = """
INSERT INTO public.wagtailimages_image(
    title, file, width, height, created_at, uploaded_by_user_id, file_size, collection_id, file_hash)
    VALUES ('{0}', '{1}', {2}, {3}, '{4}', {5}, {6}, {7}, '{8}');
"""

MEDIA_SQL_TEMPLATE = """
INSERT INTO public.wagtailmedia_media(
    title, file, type, duration, created_at, collection_id, uploaded_by_user_id)
    VALUES (?, ?, ?, 1000, ?, ?, ?);
"""

User = get_user_model()


class AssetAlreadyExistsException(Exception):
    pass


class ErrorGettingYearMonthException(Exception):
    pass


def get_month_year(key):
    # wp-content/uploads/2021/01/
    try:
        parts = key.split("/")
        target_date = datetime.date(parts[2], parts[3], 1).strftime('%B')
        return target_date.strftime("%b"), target_date.year,
    except:
        raise ErrorGettingYearMonthException()


def create_image_record(
    cursor,
    file_name,
    key,
    file_data,
    file_size,
    file_hash,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailImage.objects.filter(file=key).first():
        print("Image already exists in database, skipping")
        raise AssetAlreadyExistsException()

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
            collection_id,
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


def create_document_record(
    cursor,
    file_name,
    key,
    file_size,
    file_hash,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailDocument.objects.filter(file=key).first():
        print("Document already exists in database, skipping")
        raise AssetAlreadyExistsException()

    try:
        document_sql = DOCUMENT_SQL_TEMPLATE.format(
            file_name,
            key,
            datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            user.id,
            collection_id,
            file_size,
            file_hash,
        )
        cursor.execute(document_sql)
    except Exception as ex:
        print("COULD NOT PROCESS IMAGE, ex: ", ex)

    # Create tags
    document = WagtailDocument.objects.filter(
        file=key
    ).first()

    document.tags.add(month)


def create_media_record(
    cursor,
    file_name,
    key,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailMedia.objects.filter(file=key).first():
        print("Document already exists in database, skipping")
        raise AssetAlreadyExistsException()

    try:
        media_sql = MEDIA_SQL_TEMPLATE.format(
            file_name,
            key,
            "video",
            datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            collection_id,
            user.id,
        )
        cursor.execute(media_sql)
    except Exception as ex:
        print("COULD NOT PROCESS IMAGE, ex: ", ex)

    # Create tags
    media = WagtailMedia.objects.filter(
        file=key
    ).first()

    media.tags.add(month)


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

                year, month = get_month_year(bucket_object.key)

                collection = Collection.objects.filter(name=year).first()

                if not collection:
                    root_collection = Collection.get_first_root_node()
                    collection = root_collection.add_child(name=year)

                try:
                    if bucket_object.key.endswith(IMG_EXTENSIONS):
                        create_image_record(
                            cursor,
                            file_name,
                            bucket_object.key,
                            file_data,
                            bucket_object.size,
                            file_hash,
                            collection.id,
                            month,
                            user,
                        )
                    elif bucket_object.key.endswith(DOCUMENT_EXTENSIONS):
                        create_document_record(
                            cursor,
                            file_name,
                            bucket_object.key,
                            bucket_object.size,
                            file_hash,
                            collection.id,
                            month,
                            user,
                        )
                    elif bucket_object.key.endswith(MEDIA_EXTENSIONS):
                        create_media_record(
                            cursor,
                            file_name,
                            bucket_object.key,
                            collection.id,
                            month,
                            user,
                        )
                except AssetAlreadyExistsException:
                    continue
                except ErrorGettingYearMonthException:
                    continue
