import re
import json

from pathlib import Path
from bs4 import BeautifulSoup

from import_wordpress.utils.helpers import (
    add_paragraph_tags,
    replace_caption,
    create_image,
)


img_extensions = [".jpg", ".png", ".gif", ".webp"]


def set_content(
    author,
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

                image = create_image(
                    attachment_url,
                    file_name,
                    attachments[attachment_id]["title"],
                )
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
            block_content.append(
                {'type': 'text_section', 'value': add_paragraph_tags(content_part)},
            )

        for strong_part in strong_parts:
            # If str contains HTML, we do not want it as a heading
            if "<" in strong_part:
                text_contents.append({
                    "type": "text",
                    "value": content_part
                })
                continue

            split_strong = content_part.split(strong_part, maxsplit=1)

            #print("SPLIT STRONG", split_strong)

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

            # Process remainder
            # text_contents.append({
            #     "type": "text",
            #     "value": add_paragraph_tags(
            #         split_strong[1].replace("<strong>", "").replace("</strong>", "")
            #     )
            # })
            content_part = split_strong[1]

            #print("CONTENT PART: ", content_part)

        # TODO - figure out how to prevent the last piece of content from being rendered twice or not at all
        # Add final piece if needed
        # text_contents.append({
        #     "type": "text",
        #     "value": add_paragraph_tags(
        #         content_part.replace("<strong>", "").replace("</strong>", "")
        #     )
        # })

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

    revision = content_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()

