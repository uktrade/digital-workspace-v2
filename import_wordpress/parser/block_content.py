import re

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
    return re.sub(
        "\[caption.*\](.*)\[\/caption\]",
        replace_caption,
        content,
    )


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
            file_name = Path(attachment_url).name

            image = create_image(
                attachment_url,
                file_name,
                wp_attachments[attachment_id]["title"],
            )

            return image, alt, caption


def process_content(tag, blocks):
    print("tag", tag)
    if tag.name == "img":
        proceeding_html = flatten_parent_tags()

        blocks.append({
                'type': 'text_section',
                'value': proceeding_html
            },
        )

        image, alt, caption = process_image(tag)

        blocks.append({
                'type': 'image', 'value': {
                    'image': image,
                    'alt': alt,
                    'caption': caption,
                }
            }
        )
    else:
        if not hasattr(tag, 'contents') or len(tag.contents) == 1:
            # It's text or an element with only text inside
            if str(tag).strip() != "":
                current_parent_tags.append(str(tag).strip())
        else:
            current_parent_tags.append(unfurl_tag(tag))
            for child in tag.children:
                process_content(child, blocks)
            current_parent_tags.append(f"</{tag.name}>")


def parse_into_blocks(html_content, attachments):
    global wp_attachments
    wp_attachments = attachments

    html_content = prep_content(html_content)
    soup = BeautifulSoup(html_content, features="html5lib")

    blocks = []

    process_content(soup.body, blocks)

    # Add final HTML
    final_html = flatten_parent_tags()
    blocks.append({
            'type': 'text_section',
            'value': final_html
        },
    )

    print(blocks)


    # TODO - output is set of blocks that can be added to page
