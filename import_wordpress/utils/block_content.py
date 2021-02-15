import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from htmllaundry import sanitize
from wagtail.images.models import Image as WagtailImage
from wagtailmedia.models import Media as WagtailMedia


logger = logging.getLogger(__name__)


def flatten_parent_tags(parent_tags):
    html_str = ""
    for tag in parent_tags:
        html_str += str(tag)

    return html_str


def add_paragraph_tags(content):
    with_p = re.sub(
        r"(.+?)(?:\n|$)+",
        r"<p>\1</p>\n\n",
        content,
    )

    soup = BeautifulSoup(with_p, features="html5lib")
    body = soup.find("body")
    tidied = (
        re.sub(r"<p>\s*</p>", "", str(body))
        .replace("<body>", "")
        .replace("</body>", "")
    )

    return tidied


def replace_caption(match):
    parts = match.group(1).split(" />")

    # TODO - think about implication
    if len(parts) < 2:
        return ""

    img_string = f'{parts[0]} data-caption="{parts[1].strip()}" />'
    return img_string


def replace_video(match):
    video_details = re.findall('^.*mp4="(.*)".* poster="(.*)"', match.group(0))

    if len(video_details) == 0:
        video_details = re.findall('^.*mp4="(.*)"', match.group(0))

    video_url = video_details[0]
    video_string = f'<video src="{video_url}"></video>'

    return video_string


def prep_content(content):
    # Replace img caption [] with img tag attribute
    if not content:
        return None

    content = re.sub(
        r"\[caption.*\](.*)\[\/caption\]",
        replace_caption,
        content,
    )

    if "[video" in content:
        content = re.sub(
            r"\[video.*\](.*)\[\/video\]",
            replace_video,
            content,
        )

    # Clean up strong tags
    # content = re.sub("(<\/strong>\s*<strong>)", " ", content)

    # Add paragraph tags
    content = add_paragraph_tags(content)

    return content


def unfurl_tag(tag):
    attr_str = ""
    for key, values in tag.attrs.items():
        value_str = ""
        for v in values:
            value_str += f" {v}"
        attr_str += f'{key}="{value_str.strip()}"'

    return f"<{tag.name} {attr_str}>"


def remove_html(content):
    return BeautifulSoup(content, "lxml").text


def process_image(img, wp_attachments):
    try:
        img_classes = img["class"]
        alt = None
        caption = None

        if img.has_attr("alt"):
            alt = remove_html(img["alt"])

        if img.has_attr("data-caption"):
            caption = remove_html(img["data-caption"])

        for img_class in img_classes:
            # Check for reference to attachment
            if img_class.startswith("wp-image-"):
                attachment_id = img_class.replace("wp-image-", "")
                attachment_url = wp_attachments[attachment_id]["attachment_url"]
                parsed = urlparse(attachment_url)

                image = WagtailImage.objects.filter(file=parsed.path[1:]).first()
                return image, alt, caption
    except Exception:
        logger.error("Error processing image tag", exc_info=True)

    return None, None, None


def append_block_text(blocks, parent_tags):
    proceeding_html = flatten_parent_tags(parent_tags)
    text_content = proceeding_html.replace("<body >", "").replace("</body>", "")

    text_content_no_lb = proceeding_html.replace("\n", " ").replace("\r", "")

    if (
        text_content_no_lb.strip() != "<p >"
        and text_content_no_lb.strip() != ""  # noqa W504
        and text_content_no_lb.strip() != "&nbsp;"  # noqa W504
    ):
        blocks.append(
            {
                "type": "text_section",
                "value": sanitize(text_content).replace("<p> </p>", ""),
            },
        )


def is_heading(tag):
    try:
        if (
            (
                tag.previous_sibling
                and (  # noqa W503
                    str(tag.previous_sibling.strip()).endswith(".")
                    or tag.previous_sibling.strip() == ""  # noqa W504
                )
            )
            or not tag.previous_sibling  # noqa W504
        ) and (  # noqa W504
            (
                tag.next_sibling
                and (  # noqa W504
                    (
                        len(tag.next_sibling.strip()) > 0
                        and str(tag.next_sibling.strip())[0].isupper()  # noqa W504
                    )
                    or tag.next_sibling.strip() == ""  # noqa W504
                )
            )
            or not tag.next_sibling  # noqa W504
        ):
            return True
    except Exception:
        return False


def get_url_from_wp_guid(wp_url_guid, wp_attachments):
    for _key, value in wp_attachments.items():
        if value["guid"] == wp_url_guid:
            attachment_url = value["attachment_url"]
            parsed = urlparse(attachment_url)
            return parsed.path[1:]

    return None


def process_video(tag, attachments):
    s3_key = get_url_from_wp_guid(tag["src"], attachments)

    if s3_key is None:
        logger.info(f"CANNOT FIND VIDEO S3 KEY: {s3_key}")
        return None

    media = WagtailMedia.objects.filter(file=s3_key).first()

    if media is None:
        logger.info(f"CANNOT FIND WAGTAIL MEDIA WITH S3 KEY: {s3_key}")

    return media


# Swap out WP URL GUIDS for actual URLS
def update_href(tag, attachments):
    try:
        if tag.name == "a" and hasattr(tag, "href"):
            s3_key = get_url_from_wp_guid(tag["href"], attachments)

            from django.conf import settings

            if s3_key:
                # Will not work locally
                tag["href"] = f"https://{settings.NEW_ASSET_PATH}/{s3_key}"
                logger.info(f"UPDATE HREF TO: {tag['href']}")
    except Exception:
        logger.error("CANNOT UPDATE HREF", exc_info=True)
