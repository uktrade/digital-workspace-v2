import io
import re
import json

from pathlib import Path
from bs4 import BeautifulSoup
import requests
from io import BytesIO

from django.contrib.auth.models import User

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


def replace_caption(match):
    parts = match.group(1).split(" />")
    img_string = f'{parts[0]} data-caption="{parts[1].strip()}" />'
    return img_string


def add_paragraph_tags(content):
    return content
    test = re.sub(
        "(.+?)(?:\n|$)+",
        r"<p>\1</p>\n\n",
        content,
    )
    print("test", test)
    return test


def set_content(
    content,
    content_page,
    attachments,
):
    # Replace img caption [] with img tag attribute
    content = re.sub(
        "\[caption.*\](.*)\[\/caption\]",
        replace_caption,
        content,
    )

    soup = BeautifulSoup(content, features="html5lib")
    images = []

    for index, img in enumerate(soup.find_all("img")):
        img_classes = img["class"]
        alt = None
        caption = None

        if img.has_attr("alt"):
            alt = img["alt"]

        if img.has_attr("data-caption"):
            caption = img["data-caption"]

        for img_class in img_classes:
            # Check for reference to attachment
            if img_class.startswith("wp-image-"):
                attachment_id = img_class.replace("wp-image-", "")
                attachment_url = attachments[attachment_id]["attachment_url"]
                file_name = Path(attachment_url).name

                s3_path = attachment_url.split("?")[0].replace(
                    "https://workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com/",
                    "",
                )

                s3_bytes = download_s3_file(s3_path)

                image_bytes = io.BytesIO(s3_bytes)

                image = Image(
                    file=ImageFile(image_bytes, name=file_name),
                    title=attachments[attachment_id]["title"],
                )
                image.save()
                images.append({
                    "image": image,
                    "alt": alt,
                    "caption": caption,
                })

    starts_with_img = False

    if content.strip()[0:4] == "<img":
        starts_with_img = True

    parts = re.split('<img.*/>', content.strip())

    block_content = []
    image_counter = 0
    # parsed_first_text_block = False

    if starts_with_img:
        block_content.append({'type': 'image', 'value': {
                    'image': images[image_counter]["image"].pk,
                    'alt': images[image_counter]["alt"],
                    'caption': images[image_counter]["caption"],
                }
            }
        )
        image_counter += 1

    for content_part in parts:
        if not content_part.strip():
            continue

        strong_parts = re.findall(
            "\n\s+<strong>(.*)</strong>",
            content_part,
            flags=re.MULTILINE,
        )

        text_contents = []

        if len(strong_parts) == 0 and content_part.strip() != "":
            print("1::", content_part)
            block_content.append(
                {'type': 'text_section', 'value': add_paragraph_tags(content_part)},
            )

        for strong_part in strong_parts:
            # If str contains HTML, we do not want it as a heading
            if " <" in strong_part:
                text_contents.append({
                    "type": "text",
                    "value": content_part
                })
                continue

            split_strong = content_part.split(strong_part, maxsplit=1)

            # First part of content
            text_contents.append({
                "type": "text",
                "value": add_paragraph_tags(
                    split_strong[0].replace("<strong>", "").replace("</strong>", "")
                )
            })
            # Add string part
            text_contents.append({
                "type": "heading",
                "value": strong_part
            })
            # Set content part to remainder
            content_part = split_strong[1]

        for text_content in text_contents:
            if text_content["type"] == "heading" and text_content["value"].strip() != "":
                block_content.append(
                    {'type': 'heading2', 'value': text_content["value"]},
                )
            elif text_content["value"].strip() != "":
                block_content.append(
                    {
                        'type': 'text_section', 'value': add_paragraph_tags(
                            text_content["value"]
                        )
                    },
                )

        if image_counter < len(images):
            block_content.append({'type': 'image', 'value': {
                        'image': images[image_counter]["image"].pk,
                        'alt': images[image_counter]["alt"],
                        'caption': images[image_counter]["caption"],
                    }
                }
            )
            image_counter += 1

    content_page.body = json.dumps(block_content)

    # TODO - make user who actually created content
    user = User.objects.first()

    revision = content_page.save_revision(
        user=user,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()

    return None


