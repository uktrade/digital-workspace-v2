import io
import os
import re
import boto3
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from htmllaundry import sanitize

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile

from wagtail.core.models import Page
from wagtail.images.models import Image

from working_at_dit.models import Topic, PageTopic

legacy_s3 = boto3.client(
    's3',
    #region_name=settings.LEGACY_AWS_S3_REGION_NAME,
    aws_access_key_id=settings.LEGACY_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.LEGACY_AWS_SECRET_ACCESS_KEY,
)


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


def download_legacy_s3_file(file_name):
    s3_response_object = legacy_s3.get_object(
        Bucket=settings.LEGACY_AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
    )
    object_content = s3_response_object['Body'].read()

    return object_content


def replace_caption(match):
    parts = match.group(1).split(" />")

    # TODO - think about implication
    if len(parts) < 2:
        return ""

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
    if not settings.IMPORT_IMAGES:
        return None

    s3_path = image_url.split("?")[0].replace(
        "https://workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com/",
        "",
    )

    s3_bytes = download_legacy_s3_file(s3_path)
    image_bytes = io.BytesIO(s3_bytes)

    image = Image(
        file=ImageFile(image_bytes, name=file_name),
        title=title,
    )
    image.save()
    return image


def create_preview_image(attachments, attachment_id):
    attachment_url = attachments[attachment_id]["attachment_url"]
    parsed_url = urlparse(attachment_url)
    file_name = os.path.basename(parsed_url.path)

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
    domains = [
        "trade.gov.uk",
        "digital.trade.gov.uk",
        "trade.gsi.gov.uk",
    ]

    author = None

    # Exceptions to general pattern
    if item["creator"] == "DavidMatthews":
        item["creator"] = "David.Matthews"

    for domain in domains:
        author_email = f'{item["creator"].lower()}@{domain}'
        author = UserModel.objects.filter(
            email=author_email
        ).first()

        if author:
            break

    if not author:
        print("Could not find author: ", item["creator"])
        author = UserModel.objects.filter(
            email="connect@digital.trade.gov.uk"
        ).first()
        #raise Exception(f"Cannot find author: {author_email}")

    return author


def set_topics(content, page):
    # Set relationship with Topic pages
    if "topics" in content:
        for wp_topic in content["topics"]:
            topic = Topic.objects.filter(title=wp_topic["name"]).first()

            if not topic:  # Some topics have been archvied
                print(f'SKIPPED TOPIC: "{wp_topic["name"]}" for page {page}')
                continue

            PageTopic.objects.get_or_create(
                topic=topic,
                page=page,
            )
            page.save()
