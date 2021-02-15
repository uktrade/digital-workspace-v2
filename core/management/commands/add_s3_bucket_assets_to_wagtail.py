import hashlib
import logging
import os
from datetime import date, datetime
from io import BytesIO

import boto3
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from wagtail.core.models import Collection
from wagtail.documents.models import Document as WagtailDocument
from wagtail.images.models import Image as WagtailImage
from wagtailmedia.models import Media as WagtailMedia


logger = logging.getLogger(__name__)


DOCUMENT_EXTENSIONS = (
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".pdf",
    ".odt",
    ".dotx",
    ".xlsm",
    ".ics",
    ".txt",
    ".ppsm",
    ".ppsx",
    ".odp",
    ".xlsm",
    ".xltx",
    ".xlsb",
    ".docm",
)

IMG_EXTENSIONS = (
    ".jpg",
    ".png",
    ".webp",
    ".gif",
    ".apng",
    ".avif",
    ".jpeg",
    ".tif",
    ".tiff",
)

MEDIA_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".mp3",
    ".m4a",
)

DOCUMENT_SQL_TEMPLATE = """
INSERT INTO public.wagtaildocs_document(
    title, file, created_at, uploaded_by_user_id, collection_id, file_size, file_hash)
    VALUES ('{0}', '{1}', '{2}', {3}, {4}, {5}, '{6}');
"""

IMG_SQL_TEMPLATE = """
INSERT INTO public.wagtailimages_image(
    title, file, width, height, created_at, uploaded_by_user_id, file_size, collection_id, file_hash)
    VALUES ('{0}', '{1}', {2}, {3}, '{4}', {5}, {6}, {7}, '{8}');
"""

MEDIA_SQL_TEMPLATE = """
INSERT INTO public.wagtailmedia_media(
    title, file, type, duration, created_at, collection_id, uploaded_by_user_id, thumbnail)
    VALUES ('{0}', '{1}', '{2}', 1000, '{3}', {4}, {5}, '/assets/images/preview.png');
"""

User = get_user_model()


class ErrorCreatingAssetException(Exception):
    pass


class AssetAlreadyExistsException(Exception):
    pass


class ErrorGettingYearMonthException(Exception):
    pass


class NotFileException(Exception):
    pass


session = boto3.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

s3 = session.resource("s3")


def get_month_year(key):
    # wp-content/uploads/2021/01/
    try:
        parts = key.split("/")
        target_date = date(int(parts[2]), int(parts[3]), 1)
        return (
            target_date.strftime("%b"),
            target_date.year,
        )
    except:  # noqa B901
        raise ErrorGettingYearMonthException()


def get_file(key):
    logger.info(f"Processing object {key}")
    obj = s3.Object(
        settings.AWS_STORAGE_BUCKET_NAME,
        key,
    )
    file_data = obj.get()["Body"].read()

    if len(file_data) == 0:  # it's a "folder"
        raise NotFileException()

    file_name = os.path.basename(key)
    file_hash = hashlib.sha1(file_data).hexdigest()  # noqa S303

    return file_name, file_data, file_hash


def create_image_record(
    cursor,
    key,
    file_size,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailImage.objects.filter(file=key).first():
        logger.info("Image already exists in database, skipping")
        raise AssetAlreadyExistsException()

    file_name, file_data, file_hash = get_file(key)

    try:
        img = Image.open(BytesIO(file_data))
        image_sql = IMG_SQL_TEMPLATE.format(
            file_name,
            key,
            img.width,
            img.height,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user.id,
            file_size,
            collection_id,
            file_hash,
        )
        cursor.execute(image_sql)
    except Exception:
        logger.error("COULD NOT PROCESS IMAGE, ex: ", exc_info=True)
        raise ErrorCreatingAssetException()

    # Create tags
    image = WagtailImage.objects.filter(file=key).first()

    image.tags.add(str(month))


def create_document_record(
    cursor,
    key,
    file_size,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailDocument.objects.filter(file=key).first():
        logger.error("Document already exists in database, skipping")
        raise AssetAlreadyExistsException()

    file_name, file_data, file_hash = get_file(key)

    try:
        document_sql = DOCUMENT_SQL_TEMPLATE.format(
            file_name,
            key,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user.id,
            collection_id,
            file_size,
            file_hash,
        )
        cursor.execute(document_sql)
    except Exception:
        logger.error("COULD NOT PROCESS DOCUMENT, ex: ", exc_info=True)
        raise ErrorCreatingAssetException()

    # Create tags
    document = WagtailDocument.objects.filter(file=key).first()

    document.tags.add(str(month))


def create_media_record(
    cursor,
    key,
    collection_id,
    month,
    user,
):
    # See if image already exists
    if WagtailMedia.objects.filter(file=key).first():
        logger.error("Document already exists in database, skipping")
        raise AssetAlreadyExistsException()

    file_name = os.path.basename(key)

    try:
        media_sql = MEDIA_SQL_TEMPLATE.format(
            file_name,
            key,
            "video",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            collection_id,
            user.id,
        )
        cursor.execute(media_sql)
    except Exception:
        logger.error("COULD NOT PROCESS MEDIA RECORD, ex: ", exc_info=True)
        raise ErrorCreatingAssetException()

    # Create tags
    media = WagtailMedia.objects.filter(file=key).first()

    media.tags.add(str(month))


class Command(BaseCommand):
    help = "Generate database records for assets on S3"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            user = User.objects.first()

            if not user:
                user = get_user_model().objects.create_superuser(
                    "import_user",
                    email="import_user",
                    password=settings.IMPORT_USER_PWD,
                )

            asset_bucket = s3.Bucket(
                settings.AWS_STORAGE_BUCKET_NAME,
            )

            for bucket_object in asset_bucket.objects.all():
                try:
                    month, year = get_month_year(bucket_object.key)
                except ErrorGettingYearMonthException:
                    logger.error(
                        f"Error getting month, year for '{bucket_object.key}'",
                        exc_info=True,
                    )
                    continue

                collection = Collection.objects.filter(name=year).first()

                if not collection:
                    root_collection = Collection.get_first_root_node()
                    collection = root_collection.add_child(name=str(year))

                try:
                    if bucket_object.key.endswith(IMG_EXTENSIONS):
                        create_image_record(
                            cursor,
                            bucket_object.key,
                            bucket_object.size,
                            collection.id,
                            month,
                            user,
                        )
                    elif bucket_object.key.endswith(DOCUMENT_EXTENSIONS):
                        create_document_record(
                            cursor,
                            bucket_object.key,
                            bucket_object.size,
                            collection.id,
                            month,
                            user,
                        )
                    elif bucket_object.key.endswith(MEDIA_EXTENSIONS):
                        create_media_record(
                            cursor,
                            bucket_object.key,
                            collection.id,
                            month,
                            user,
                        )
                    elif "." in bucket_object.key:  # want to ignore folders
                        logger.info(f"CANNOT MAP EXTENSION for {bucket_object.key}")
                except AssetAlreadyExistsException:
                    continue
                except ErrorCreatingAssetException:
                    continue
                except NotFileException:
                    continue
