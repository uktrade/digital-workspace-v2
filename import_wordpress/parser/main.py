import os
import re
from datetime import datetime
from phpserialize import unserialize

from django.contrib.auth import get_user_model

import xml.etree.ElementTree as element_tree

from wagtail.core.models import Page

from import_wordpress.parser.comments import get_comments
from import_wordpress.parser.wagtail_content.news import create_news_page
from import_wordpress.parser.wagtail_content.theme import create_theme
from import_wordpress.parser.wagtail_content.topic import create_topic
from import_wordpress.parser.wagtail_content.how_do_i import create_how_do_i
from import_wordpress.parser.wagtail_content.policy_or_guidance import (
    create_policy_or_guidance,
)
from import_wordpress.parser.users import create_users
from import_wordpress.utils.page_hierarchy import create_section_homepages
from import_wordpress.utils.page import populate_page

from import_wordpress.utils.orphans import (
    orphan_policy,
    orphan_guidance,
)

from django.conf import settings

namespaces = settings.NAMESPACES

UserModel = get_user_model()

xml_file = os.path.join(settings.BASE_DIR, "wordpress.xml")

counter = 0

objects = [
    "Title",
    "File",
    # ...
]

post_types = [
    'acf-field',
    'acf-field-group',
    'attachment',
    'howdoi',
    'menu',
    'news',
    'page',
    'policy',
    'popular_page',
    'theme',
    'post',
    'topic',
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

tag_names = [
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

# Swap policies and guidance URLs


root = element_tree.parse(xml_file).getroot()

# Update paths


skip_list = [
    "/sectors/technology-and-smart-cities/",
]

# TODO - create redirects
orphans = {
    "/dits-history/": "/about-us/dits-history/",
    "/how-we-are-structured/": "/about-us/how-we-are-structured/",
    "/lpg/": "/about-us/lpg/",
    "/our-management/": "/about-us/our-management/",
    "/our-ministers/": "/about-us/our-ministers/",
    "/our-unions/": "/about-us/our-unions/",
    "/our-vision-mission-and-values/": "/about-us/our-vision-mission-and-values/",
    "/single-departmental-plan/": "/about-us/single-departmental-plan/",
}


def parse_xml_file():
    # delete all pages
    Page.objects.all().exclude(slug="home").exclude(slug="root").delete()

    create_section_homepages()
    create_users(root)

    processed_items = []

    # Iterate through Wordpress structures - "item" is a types of content, including pages
    # First step is to create a structure that we can use to create Wagtail content
    for item_tag in root.find("channel").findall('item'):
        item = {}

        for tag_name in tag_names:
            tag = item_tag.find(tag_name, namespaces)

            if hasattr(tag, "text"):
                cleaned_tag_name = tag_name.replace("wp:", "").replace(":encoded", "")
                item[cleaned_tag_name] = tag.text
                # Add default for title
                if tag_name == "title" and item[cleaned_tag_name] is None:
                    item["tite"] = "NO TITLE"
            else:
                print("Could not find tag: ", tag_name)

        post_id_tag = item_tag.find("wp:post_id", namespaces)
        post_type_tag = item_tag.find("wp:post_type", namespaces)
        post_date = item_tag.find("wp:post_date", namespaces)
        pub_date = item_tag.find("pubDate", namespaces)

        item["categories"] = []
        item["topics"] = []
        item["themes"] = []

        category_tags = item_tag.findall("category")

        for category_tag in category_tags:
            if category_tag.get("domain") == "news_category":
                item["categories"].append(category_tag.text)
            if category_tag.get("domain") == "topic_taxonomy":
                item["topics"].append({
                    "name": category_tag.text,
                    "nice_name": category_tag.get("nicename"),
                })
            if category_tag.get("domain") == "theme_taxonomy":
                item["themes"].append({
                    "name": category_tag.text,
                    "nice_name": category_tag.get("nicename"),
                })

        item["post_date"] = datetime.strptime(
            post_date.text,
            '%Y-%m-%d %H:%M:%S',
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
                    '%a, %d %b %Y %H:%M:%S %z',
                )
            else:
                item["pub_date"] = None

        item["creator"] = item_tag.find("dc:creator", namespaces).text
        post_meta_tags = item_tag.findall("wp:postmeta", namespaces)

        item["documents"] = []

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
            if re.match("documents_[0-9]+_title", meta_key_tag.text):
                item["documents"].append(meta_value_tag.text)

            # Redirect
            if meta_key_tag.text == "redirect_url":
                if meta_value_tag.text:
                    converted_php = unserialize(str.encode(meta_value_tag.text))
                    item["redirect_url"] = converted_php[b"url"].decode("utf-8")

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

    print("Creating themes...")

    # Themes
    for key, value in items["theme"].items():
        create_theme(
            items["theme"][key],
        )

    print("Creating topics...")

    # Topics
    for key, value in items["topic"].items():
        create_topic(
            items["topic"][key],
            items["attachment"],
        )

    print("Creating news...")

    # News
    for key, value in items["news"].items():
        create_news_page(
            items["news"][key],
            items["attachment"]
        )

    print("Creating page content...")

    # Page content
    for key, value in items["page"].items():
        if value["status"] == "publish":
            populate_page(
                value["link"],
                items,
            )

    print("Creating how do Is...")

    # How do I content
    for key, value in items["howdoi"].items():
        create_how_do_i(
            items["howdoi"][key],
            items["attachment"],
        )

    print("Creating policies and guidance...")

    # Policies and guidance
    for key, value in items["policy"].items():
        create_policy_or_guidance(
            items["policy"][key],
            items["attachment"],
        )

    print("Document links found:")
    for item in processed_items:
        if item["documents"]:
            for document in item["documents"]:
                print(f'{item["link"]}\t{document}\n')
