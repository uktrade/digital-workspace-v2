import logging
import re
from datetime import datetime

from defusedxml import ElementTree
from django.conf import settings
from django.contrib.auth import get_user_model
from phpserialize import unserialize
from wagtail.core.models import Page

from import_wordpress.parser.comments import get_comments
from import_wordpress.parser.users import create_users
from import_wordpress.parser.wagtail_content.how_do_i import HowDoIPage
from import_wordpress.parser.wagtail_content.news import WagtailNewsPage
from import_wordpress.parser.wagtail_content.policy_or_guidance import (
    PolicyOrGuidancePage,
)
from import_wordpress.parser.wagtail_content.theme import create_theme
from import_wordpress.parser.wagtail_content.topic import TopicPage
from import_wordpress.utils.orphans import orphan_guidance, orphan_policy
from import_wordpress.utils.page import populate_page
from import_wordpress.utils.page_hierarchy import create_section_homepages


logger = logging.getLogger(__name__)

namespaces = settings.NAMESPACES

UserModel = get_user_model()


TAG_NAMES = [
    "title",
    "content:encoded",
    "wp:post_parent",
    "wp:post_name",
    "wp:status",
    "wp:post_id",
    "wp:post_type",
    "wp:status",
    "link",
    "guid",
    "wp:attachment_url",
]

items = {
    "acf_field": {},
    "acf_field_group": {},
    "attachment": {},
    "howdoi": {},
    "menu": {},
    "news": {},
    "page": {},
    "policy": {},
    "popular_page": {},
    "theme": {},
    "post": {},
    "topic": {},
}

skip_list = settings.SKIP_LIST

# TODO - create redirects
orphans = settings.ORPHAN_PAGES


def parse_xml_file(xml_file):
    with open(xml_file, "r+") as f:
        text = f.read()
        for asset_path in settings.OLD_ASSET_PATHS:
            text = text.replace(
                asset_path,
                settings.NEW_ASSET_PATH,
            )
        f.seek(0)
        f.write(text)
        f.truncate()

    root = ElementTree.parse(xml_file).getroot()

    # delete all pages
    Page.objects.all().exclude(slug="home").exclude(slug="root").delete()

    create_section_homepages()
    create_users(root)

    processed_items = []

    # Iterate through Wordpress structures - "item" is a types of content, including pages
    # First step is to create a structure that we can use to create Wagtail content
    for item_tag in root.find("channel").findall("item"):
        item = {}

        for tag_name in TAG_NAMES:
            tag = item_tag.find(tag_name, namespaces)

            if hasattr(tag, "text"):
                cleaned_tag_name = tag_name.replace("wp:", "").replace(":encoded", "")
                item[cleaned_tag_name] = tag.text
                #  Add default for title
                if tag_name == "title" and item[cleaned_tag_name] is None:
                    item["title"] = "NO TITLE"
            else:
                logger.warning(f"Could not find tag: '{tag_name}'")

        # Check for topic that has not actually been published
        if "/?post_type=topic" in item["link"]:
            continue

        post_id_tag = item_tag.find("wp:post_id", namespaces)
        post_type_tag = item_tag.find("wp:post_type", namespaces)
        post_date = item_tag.find("wp:post_date", namespaces)
        pub_date = item_tag.find("pubDate", namespaces)

        item["categories"] = []
        item["topics"] = []
        item["themes"] = []
        item["search_pinned"] = []
        item["search_excluded"] = []

        category_tags = item_tag.findall("category")

        for category_tag in category_tags:
            if category_tag.get("domain") == "news_category":
                item["categories"].append(category_tag.text)
            if category_tag.get("domain") == "topic_taxonomy":
                item["topics"].append(
                    {
                        "name": category_tag.text,
                        "nice_name": category_tag.get("nicename"),
                    }
                )
            if category_tag.get("domain") == "theme_taxonomy":
                item["themes"].append(
                    {
                        "name": category_tag.text,
                        "nice_name": category_tag.get("nicename"),
                    }
                )

        item["post_date"] = datetime.strptime(
            post_date.text,
            "%Y-%m-%d %H:%M:%S",
        )
        if hasattr(pub_date, "text"):
            # Fri, 17 Jul 2020 10:00:07 +0000
            pub_date_text = pub_date.text

            if pub_date_text:
                if "-0001 00:00:00 +0000" in pub_date_text:
                    pub_date_text = pub_date_text.replace(
                        "-0001",
                        "2000",
                    )

                item["pub_date"] = datetime.strptime(
                    pub_date_text,
                    "%a, %d %b %Y %H:%M:%S %z",
                )
            else:
                item["pub_date"] = None

        item["creator"] = item_tag.find("dc:creator", namespaces).text
        post_meta_tags = item_tag.findall("wp:postmeta", namespaces)

        item["document_titles"] = []
        item["document_files"] = []

        for post_meta_tag in post_meta_tags:
            meta_key_tag = post_meta_tag.find("wp:meta_key", namespaces)
            meta_value_tag = post_meta_tag.find("wp:meta_value", namespaces)

            # Get preview image
            if meta_key_tag.text == "image":
                item["preview_image_id"] = meta_value_tag.text

            # Get excerpt
            if meta_key_tag.text == "excerpt":
                item["excerpt"] = meta_value_tag.text

            # Policy or guidance
            if meta_key_tag.text == "policy_or_guidance":
                item["policy_or_guidance"] = meta_value_tag.text

            # Documents
            # if re.match("documents_[0-9]+_title", meta_key_tag.text):
            #     item["document_titles"].append(meta_value_tag.text)

            if re.match("documents_[0-9]+_file", meta_key_tag.text):
                item["document_files"].append(meta_value_tag.text)

            # Redirect
            if meta_key_tag.text == "redirect_url":
                if meta_value_tag.text:
                    converted_php = unserialize(str.encode(meta_value_tag.text))
                    item["redirect_url"] = converted_php[b"url"].decode("utf-8")

            # Relevanssi pin
            if meta_key_tag.text == "_relevanssi_pin":
                if meta_value_tag.text and meta_value_tag.text != "":
                    item["search_pinned"].append(meta_value_tag.text)

            # Relevanssi exclude
            if meta_key_tag.text == "_relevanssi_unpin":
                if meta_value_tag.text and meta_value_tag.text != "":
                    item["search_excluded"].append(meta_value_tag.text)

        # News comments
        item["comments"] = get_comments(item_tag)

        post_type = post_type_tag.text.replace("wp:", "").replace("-", "_")
        post_id = post_id_tag.text

        if not post_id:
            post_id = item["link"].replace("/?attachment_id=", "")

        if item["link"] not in skip_list:
            if item["link"] in orphans:
                item["link"] = orphans[item["link"]]

            if item["link"] in orphan_guidance:
                item["policy_or_guidance"] = "guidance"
                items["policy"][post_id] = item
            elif item["link"] in orphan_policy:
                items["policy"][post_id] = item
                item["policy_or_guidance"] = "policy"
            else:
                items[post_type][post_id] = item

        processed_items.append(item)

    # Second step is to generate Wagtail content
    logger.info("Creating themes...")

    # Themes
    for key, _value in items["theme"].items():
        create_theme(
            items["theme"][key],
        )

    logger.info("Creating topics...")

    # Topics
    for key, _value in items["topic"].items():
        topic_page = TopicPage(
            page_content=items["topic"][key],
            attachments=items["attachment"],
        )
        if topic_page.live:
            topic_page.create()

    logger.info("Creating news...")

    # News
    for key, _value in items["news"].items():
        news_page = WagtailNewsPage(
            page_content=items["news"][key],
            attachments=items["attachment"],
        )
        if news_page.live:
            news_page.create()

    # Page content
    for _key, value in items["page"].items():
        if value["status"] == "publish":
            populate_page(
                value["link"],
                items,
            )

    logger.info("Creating how do Is...")

    # How do I content
    for key, _value in items["howdoi"].items():
        how_do_i = HowDoIPage(
            page_content=items["howdoi"][key],
            attachments=items["attachment"],
        )
        if how_do_i.live:
            how_do_i.create()

    logger.info("Creating policies and guidance...")

    # Policies and guidance
    for key, _value in items["policy"].items():
        policy_or_guidance = PolicyOrGuidancePage(
            page_content=items["policy"][key],
            attachments=items["attachment"],
        )
        if policy_or_guidance.live:
            policy_or_guidance.create()
