import io

from bs4 import BeautifulSoup
import requests
from io import BytesIO
from django.core.files.images import ImageFile
from urllib.parse import urlparse

from django.core.files.base import ContentFile

from wagtail.images.models import Image

from .utils import (
    convert_domain,
    download_s3_file,
)


img_extensions = [".jpg", ".png", ".gif", ".webp"]


def is_image(post_data):
    for img_extension in img_extensions:
        if post_data["postmeta"]["attached_file"].endswith(img_extension):
            return True

    return False


def get_image_properties(post_data):
    name = post_data['postmeta']["attachment_metadata"][b"file"]
    url = f"https://static.workspace.trade.gov.uk/wp-content/uploads/{post_data['postmeta']['attached_file']}"
    width = int(post_data['postmeta']["attachment_metadata"][b"width"])
    height = int(post_data['postmeta']["attachment_metadata"][b"height"])

    print("width", width)
    print("height", height)

    return name, url, width, height


def get_preview_image(content):
    pass


def set_content(
    content,
    content_page,
    attachments,
):
    soup = BeautifulSoup(content)

    for index, img in enumerate(soup.find_all('img')):
        img_classes = img['class']

        for img_class in img_classes:
            # Check for reference to attachment
            if img_class.startswith("wp-image-"):
                attachment_id = img_class.replace("wp-image-", "")
                attachment_url = attachments[attachment_id]["attachment_url"]

                s3_path = attachment_url.split("?")[0].replace(
                    "https://workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com/",
                    "",
                )

                print("s3_path", s3_path)

                s3_bytes = download_s3_file(s3_path)

                image_bytes = io.BytesIO(s3_bytes)

                image = Image(
                    file=ImageFile(image_bytes, name="test.jpg"),
                    title="test",
                )
                image.save()

    return None


