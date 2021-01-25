import re
import boto3

from bs4 import BeautifulSoup

from htmllaundry import sanitize

from django.conf import settings
from django.contrib.auth import get_user_model

from wagtail.core.models import Page
from wagtail.images.models import Image as WagtailImage

from working_at_dit.models import Topic, PageTopic

legacy_s3 = boto3.client(
    's3',
    #region_name=settings.LEGACY_AWS_S3_REGION_NAME,
    aws_access_key_id=settings.LEGACY_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.LEGACY_AWS_SECRET_ACCESS_KEY,
)


UserModel = get_user_model()


def is_live(status):
    if status == "publish":
        return True

    return False


def replace_caption(match):
    parts = match.group(1).split(" />")

    # TODO - think about implication
    if len(parts) < 2:
        return ""

    img_string = f'{parts[0]} data-caption="{parts[1].strip()}" />'
    return img_string


def replace_video(match):
    video_details = re.findall('^.*mp4="(.*)".* poster="(.*)"', match.group(1))
    video_url = video_details[0]
    poster = video_details[1]

    video_string = f"""
    <video preload="meta" controls class="ws-streamfield-content__media" poster="{poster}">
        <source src="{video_url}" type="video/mp4" />
        <p class="govuk-body">
            Video file:
            <a href="{video_url}">Download</a>
        </p>
    </video>
    """

    return video_string


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


def get_asset_path(get_asset_path):
    return re.findall(
        "https://static.workspace.trade.gov.uk/(.*)\?",
        get_asset_path
    )[0]


def get_preview_image(attachments, attachment_id):
    attachment_url = attachments[attachment_id]["attachment_url"]
    asset_path = get_asset_path(attachment_url)

    return WagtailImage.objects.filter(file=asset_path)


def get_slug(slug, counter=1):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-{counter}", (counter + 1))

    return slug


def get_author(item):
    domains = [
        "trade.gov.uk",
        "digital.trade.gov.uk",
        "trade.gsi.gov.uk",
    ]

    author = None

    # Exceptions to general pattern
    if item["creator"] == settings.AUTHOR_TO_BE_SUBSTITUTED:
        item["creator"] = settings.AUTHOR_SUBSTITUTED

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
