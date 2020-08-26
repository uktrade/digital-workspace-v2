import io
import re
import boto3

from pathlib import Path
from bs4 import BeautifulSoup

from htmllaundry import sanitize

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile

from wagtail.core.models import Page
from wagtail.images.models import Image


s3 = boto3.client('s3')


UserModel = get_user_model()


legacy_domains = [
    'digital-workspace-staging.london.cloudapps.digital',
    'api.workspace.trade.uat.uktrade.io',
    'admin.workspace.trade.uat.uktrade.io',
    'admin.workspace.trade.gov.uk',
    'digital-workspace-dev.london.cloudapps.digital',
    'dit.useconnect.co.uk',
]

asset_domain = "workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com"


def convert_domain(src_value):
    for legacy_domain in legacy_domains:
        src_value = src_value.replace(legacy_domain, asset_domain)

    return src_value


def is_live(status):
    if status == "publish":
        return True

    return False


def download_s3_file(file_name):
    s3_response_object = s3.get_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
    )
    object_content = s3_response_object['Body'].read()

    return object_content


def replace_caption(match):
    parts = match.group(1).split(" />")
    img_string = f'{parts[0]} data-caption="{parts[1].strip()}" />'
    return img_string


def add_paragraph_tags(content):
    with_p = re.sub(
        "(.+?)(?:\n|$)+",
        r"<p>\1</p>\n\n",
        content,
    )

    with_p = sanitize(with_p)

    soup = BeautifulSoup(with_p, features="html5lib")
    body = soup.find("body")
    tidied = re.sub("<p>\s*</p>", "", str(body)).replace("<body>", "").replace("</body>", "")

    return tidied


def create_image(image_url, file_name, title):
    s3_path = image_url.split("?")[0].replace(
        "https://workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com/",
        "",
    )

    s3_bytes = download_s3_file(s3_path)
    image_bytes = io.BytesIO(s3_bytes)

    image = Image(
        file=ImageFile(image_bytes, name=file_name),
        title=title,
    )
    image.save()
    return image


def create_preview_image(attachments, attachment_id):
    attachment_url = attachments[attachment_id]["attachment_url"]
    file_name = Path(attachment_url).name

    return create_image(
        attachment_url,
        file_name,
        attachments[attachment_id]["title"],
    )


def get_slug(slug):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-1")

    return slug


def get_author(item):
    author_email = f'{item["creator"]}@trade.gov.uk'
    author = UserModel.objects.filter(email=author_email).first()

    if not author:
        author_email = f'{item["creator"]}@digital.trade.gov.uk'
        author = UserModel.objects.filter(email=author_email).first()

    if not author:
        raise Exception(f"Cannot find author: {author_email}")

    return author
