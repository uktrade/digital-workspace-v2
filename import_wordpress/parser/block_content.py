import logging

from bs4 import BeautifulSoup

from import_wordpress.utils.block_content import (
    append_block_text,
    is_heading,
    prep_content,
    process_image,
    process_video,
    unfurl_tag,
    update_href,
)

wp_attachments = None

current_parent_tags = []


logger = logging.getLogger(__name__)


def process_content(tag, blocks, depth, attachments):
    update_href(tag, attachments)

    if tag.name == "img":
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        image, alt, caption = process_image(tag, attachments)

        if image:
            blocks.append(
                {
                    "type": "image",
                    "value": {
                        "image": image.pk,
                        "alt": alt,
                        "caption": caption,
                    },
                }
            )
        else:
            logger.error("CANNOT FIND IMAGE")
    elif tag.name == "video":
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        media = process_video(tag, attachments)

        if media:
            blocks.append(
                {
                    "type": "media",
                    "value": {
                        "media_file": media.id,
                    },
                }
            )
    elif tag.name == "strong" and depth == 3 and is_heading(tag):
        # If this is level 3, swap for header tag
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        blocks.append({"type": "heading2", "value": tag.text})
    elif (tag.name == "h1" or tag.name == "h2") and depth == 2:
        # If this is level 3, swap for header tag
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        blocks.append({"type": "heading2", "value": tag.text})
    elif tag.name == "h3" and depth == 2:
        # If this is level 3, swap for header tag
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        blocks.append({"type": "heading3", "value": tag.text})
    elif tag.name == "h4" and depth == 2:
        # If this is level 3, swap for header tag
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        blocks.append({"type": "heading4", "value": tag.text})
    elif tag.name == "h5" and depth == 2:
        # If this is level 3, swap for header tag
        append_block_text(blocks, current_parent_tags)
        current_parent_tags.clear()
        blocks.append({"type": "heading5", "value": tag.text})
    else:
        if not hasattr(tag, "contents") or (
            len(tag.contents) == 1 and tag.contents[0].name is None
        ):
            # It's text or an element with only text inside
            if str(tag).strip() != "":
                current_parent_tags.append(f" {str(tag).strip()} ")
        else:
            current_parent_tags.append(unfurl_tag(tag))
            depth += 1
            for child in tag.children:
                process_content(child, blocks, depth, attachments)
            current_parent_tags.append(f"</{tag.name}>")

    #  remove all classes (there's stuff left over from Word pastes etc)
    if hasattr(tag, "attrs"):
        for attribute in [
            "class",
            "name",
            "style",
            "width",
        ]:
            del tag[attribute]


def parse_into_blocks(html_content, attachments):
    if not html_content:
        return None

    html_content = prep_content(html_content)
    soup = BeautifulSoup(html_content, features="html5lib")

    blocks = []

    # Process HTML into Wagtail StreamField blocks
    process_content(soup.body, blocks, 1, attachments)

    # Add final HTML
    append_block_text(blocks, current_parent_tags)
    current_parent_tags.clear()

    return blocks
