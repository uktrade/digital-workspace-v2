import os
import re
from urllib.parse import urlparse

from pathlib import Path
from bs4 import BeautifulSoup

from import_wordpress.utils.helpers import (
    add_paragraph_tags,
    replace_caption,
    create_image,
)


wp_attachments = None

current_parent_tags = []


def prep_content(content):
    # Replace img caption [] with img tag attribute
    content = re.sub(
        "\[caption.*\](.*)\[\/caption\]",
        replace_caption,
        content,
    )

    # Clean up strong tags
    return re.sub("(<\/strong>\s*<strong>)", "", content)


def flatten_parent_tags():
    html_str = ""
    for tag in current_parent_tags:
        html_str += str(tag)

    current_parent_tags.clear()
    return html_str


def unfurl_tag(tag):
    attr_str = ""
    for key, values in tag.attrs.items():
        value_str = ""
        for v in values:
            value_str += f" {v}"
        attr_str += f"{key}=\"{value_str.strip()}\""

    return f"<{tag.name} {attr_str}>"


def process_image(img):
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
            attachment_url = wp_attachments[attachment_id]["attachment_url"]
            parsed_url = urlparse(attachment_url)
            file_name = os.path.basename(parsed_url.path)

            image = create_image(
                attachment_url,
                file_name,
                wp_attachments[attachment_id]["title"],
            )

            return image, alt, caption


def append_block_text(blocks):
    proceeding_html = flatten_parent_tags()
    text_content = proceeding_html.replace("<body >", "").replace("</body>", "")

    if text_content != "":
        blocks.append({
                'type': 'text_section',
                'value': add_paragraph_tags(text_content)
            },
        )


def is_heading(tag):
    if (
            (
                (
                    tag.previous_sibling and
                    (
                        str(tag.previous_sibling.strip()).endswith(".") or
                        tag.previous_sibling.strip() == ""
                    )
                )
                or
                    not tag.previous_sibling
            )
            and
            (
                (
                    tag.next_sibling and
                    (
                        (
                            len(tag.next_sibling.strip()) > 0 and
                            str(tag.next_sibling.strip())[0].isupper()
                        ) or
                            tag.next_sibling.strip() == ""
                    )
                )
                or
                    not tag.next_sibling
            )
    ):
        return True

    return False


def process_content(tag, blocks, depth):
    if tag.name == "img":
        append_block_text(blocks)

        image, alt, caption = process_image(tag)

        blocks.append({
                'type': 'image', 'value': {
                    'image': image.pk,
                    'alt': alt,
                    'caption': caption,
                }
            }
        )
    elif tag.name == "strong" and depth == 2 and is_heading(tag):
        # If this is level 2, swap for header tag
        append_block_text(blocks)

        blocks.append({
            "type": "heading2",
            "value": tag.text
        })
    else:
        if not hasattr(tag, 'contents') or len(tag.contents) == 1:
            # It's text or an element with only text inside
            if str(tag).strip() != "":
                current_parent_tags.append(f" {str(tag).strip()} ")
        else:
            current_parent_tags.append(unfurl_tag(tag))
            depth += 1
            for child in tag.children:
                process_content(child, blocks, depth)
            current_parent_tags.append(f"</{tag.name}>")


def parse_into_blocks(html_content, attachments):
    global wp_attachments
    wp_attachments = attachments

    html_content = prep_content(html_content)
    soup = BeautifulSoup(html_content, features="html5lib")

    blocks = []

    # Process HTML into Wagtail StreamField blocks
    process_content(soup.body, blocks, 1)

    # Add final HTML
    append_block_text(blocks)

    return blocks
