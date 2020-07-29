import os
import uuid
from datetime import datetime

import requests

import wpparser

from django.conf import settings
from django.contrib.auth import get_user_model

from django.core.files.images import ImageFile
from django.template.defaultfilters import slugify

from urllib.request import urlopen
from urllib.parse import urlparse
from io import BytesIO
from django.core.files.images import ImageFile

from phpserialize import loads as php_loads


import xml.etree.ElementTree as element_tree

from wagtail.core.models import Page
from wagtail.images.models import Image

from content.models import (
    ContentPage,
    NewsHome,
    NewsPage,
    NewsCategoryTag,
    TaggedNews,
    Comment,
)

from .image import (
    create_preview_image,
    set_content,
)

from .utils import (
    is_live,
)

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


def get_slug(slug):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-1")

    return slug


def create_news_home(home_page, post_date):
    news_home = NewsHome(
        # path="news-and-views",
        title="All News",
        slug="news-and-views",
        live=True,
        first_published_at=post_date,
    )

    home_page.add_child(instance=news_home)
    home_page.save()
    return NewsHome.objects.all().first()


processed_categories = []


def create_comment(comment, content_page, comments):
    # Check to see if comment exists (could have been made as a parent)
    existing_comment = Comment.objects.filter(
        legacy_id=int(comment["legacy_id"]),
    ).first()

    if existing_comment:
        return existing_comment

    # Check for parent
    parent_comment = None

    if comment["parent_id"] != '0':
        parent_comment = Comment.objects.filter(
            legacy_id=int(comment["parent_id"]),
        ).first()

        if not parent_comment:
            # Get parent comment
            for c in comments:
                if c["legacy_id"] == comment["parent"]:
                    parent_comment = create_comment(c, content_page, comments)

    author = UserModel.objects.filter(email=comment["author_email"]).first()

    assert author is not None

    return Comment.objects.create(
        legacy_id=int(comment["legacy_id"]),
        author=author,
        news_page=content_page,
        content=comment["content"],
        parent=parent_comment,
    )


def create_news_page(
    home_page,
    news_item,
    attachments,
):
    # check for existence of parent news page
    news_home = Page.objects.filter(slug="news-and-views").first()
    if not news_home:
        news_home = create_news_home(home_page, news_item["post_date"])

    path = get_slug(
        news_item["link"].replace(
            "/news-and-views",
            "",
        )
    )
    live = is_live(news_item["status"])

    author_email = f'{news_item["creator"]}@trade.gov.uk'
    author = UserModel.objects.filter(email=author_email).first()

    if not author:
        author_email = f'{news_item["creator"]}@digital.trade.gov.uk'
        author = UserModel.objects.filter(email=author_email).first()

    if not author:
        raise Exception(f"Cannot find author: {author_email}")

    if "preview_image_id" in news_item:
        preview_image = create_preview_image(
            attachments,
            news_item["preview_image_id"],
        )

        content_page = NewsPage(
            first_published_at=news_item["pub_date"],
            last_published_at=news_item["post_date"],
            title=news_item["title"],
            slug=slugify(path),
            legacy_guid=news_item["guid"],
            legacy_content=news_item["content"],
            live=live,
            hero_image=preview_image,
            excerpt=news_item["excerpt"]
        )
    else:
        content_page = NewsPage(
            first_published_at=news_item["pub_date"],
            last_published_at=news_item["post_date"],
            title=news_item["title"],
            slug=slugify(path),
            legacy_guid=news_item["guid"],
            legacy_content=news_item["content"],
            live=live,
            excerpt=news_item["excerpt"]
        )

    news_home.add_child(instance=content_page)
    news_home.save()

    # Set categories
    if "categories" in news_item:
        for category in news_item["categories"]:
            if category not in processed_categories:
                news_category = NewsCategoryTag(
                    name=category,
                    slug=slugify(category),
                )
                news_category.save()

                tagged_news = TaggedNews(
                    tag=news_category,
                    content_object=content_page,
                )
                tagged_news.save()

                processed_categories.append(category)

    # Comments
    for comment in news_item["comments"]:
        create_comment(
            comment,
            content_page,
            news_item["comments"],
        )

    # get preview image from HTML
    set_content(
        author,
        news_item["content"],
        content_page,
        attachments,
    )


namespaces = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}

root = element_tree.parse(xml_file).getroot()


def parse_xml_file():
    home_page = Page.objects.filter(slug="home").first()

    # Parse out users
    for author in root.find("channel").findall('wp:author', namespaces):
        email = author.find("wp:author_email", namespaces).text
        first_name = author.find("wp:author_first_name", namespaces).text
        last_name = author.find("wp:author_last_name", namespaces).text

        if not first_name:
            first_name = ""

        if not last_name:
            last_name = ""

        user = UserModel(
            username=uuid.uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()

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
        "wp:status",
        "wp:post_id",
        "wp:post_type",
        "wp:status",
        "link",
        "guid",
        "wp:attachment_url",
    ]

    for item_tag in root.find("channel").findall('item'):
        item = {}

        for tag_name in tag_names:
            tag = item_tag.find(tag_name, namespaces)

            if hasattr(tag, "text"):
                item[tag_name.replace("wp:", "").replace(":encoded", "")] = tag.text
            else:
                print("Could not find tag: ", tag_name)

        post_id_tag = item_tag.find("wp:post_id", namespaces)
        post_type_tag = item_tag.find("wp:post_type", namespaces)
        post_date = item_tag.find("wp:post_date", namespaces)
        pub_date = item_tag.find("pubDate", namespaces)

        item["categories"] = []

        category_tags = item_tag.findall("category")

        for category_tag in category_tags:
            if category_tag.get("domain") == "news_category":
                item["categories"].append(category_tag.text)

        item["post_date"] = datetime.strptime(
            post_date.text,
            '%Y-%m-%d %H:%M:%S',
        )
        if hasattr(pub_date, "text"):
            # Fri, 17 Jul 2020 10:00:07 +0000
            item["pub_date"] = datetime.strptime(
                pub_date.text,
                '%a, %d %b %Y %H:%M:%S %z',
            )

        item["creator"] = item_tag.find("dc:creator", namespaces).text
        post_meta_tags = item_tag.findall("wp:postmeta", namespaces)

        for post_meta_tag in post_meta_tags:
            meta_key_tag = post_meta_tag.find("wp:meta_key", namespaces)
            meta_value_tag = post_meta_tag.find("wp:meta_value", namespaces)

            # Get preview image
            if meta_key_tag.text == "image":
                item["preview_image_id"] = meta_value_tag.text

            # Get excerpt
            if meta_key_tag.text == "excerpt":
                item["excerpt"] = meta_value_tag.text

            # if meta_key_tag.text == "amazonS3_cache":
            #     s3_cache_php = meta_value_tag.text
            #     s3_cache = php_loads(bytes(s3_cache_php, encoding='utf-8'))
            #
            #     print(s3_cache)

        # Comments
        item["comments"] = []

        comment_tags = item_tag.findall("wp:comment", namespaces)

        for comment_tag in comment_tags:
            comment_id = comment_tag.find("wp:comment_id", namespaces).text
            author_email = comment_tag.find("wp:comment_author_email", namespaces).text
            comment_date = datetime.strptime(
                comment_tag.find("wp:comment_date", namespaces).text,
                '%Y-%m-%d %H:%M:%S',
            )
            content = comment_tag.find("wp:comment_content", namespaces).text
            parent_id = comment_tag.find("wp:comment_parent", namespaces).text
            item["comments"].append({
                "comment_id": comment_id,
                "author_email": author_email,
                "comment_date": comment_date,
                "content": content,
                "parent_id": parent_id,
                "legacy_id": comment_id
            })

        post_type = post_type_tag.text.replace("wp:", "").replace("-", "_")
        post_id = post_id_tag.text

        if not post_id:
            post_id = item["link"].replace("/?attachment_id=", "")

        items[post_type][post_id] = item

    # News
    for key, value in items["news"].items():
        create_news_page(
            home_page,
            items["news"][key],
            items["attachment"]
        )

    # return
    #
    # for post in wp_data["posts"]:
    #     title = "Placeholder..."
    #
    #     if "title" in post and post["title"] not in (None, ""):
    #         title = post["title"]
    #
    #     legacy_guid = post["guid"]
    #
    #     if "post_type" in post:
    #         # # Images
    #         # if post["post_type"] == "attachment":
    #         #     continue
    #         #     if is_image(post):
    #         #         img_name, img_url, img_w, img_h = get_image_properties(post)
    #         #         #img_file = BytesIO(urlopen(img_url).read())
    #         #
    #         #         http_res = requests.get(img_url)
    #         #         image_file = ImageFile(BytesIO(http_res.content), name=img_name.decode("utf-8"))
    #         #         image = Image(title=title, file=image_file, width=1, height=1)
    #         #         image.save()
    #         #
    #         #         print("img_name", img_name.decode("utf-8") )
    #         #         print("img_url", img_url)
    #         #         print("img_w", img_w)
    #         #         print("img_h", img_h)
    #         #         #
    #         #         # Image.objects.create(
    #         #         #     title="Image title",
    #         #         #     # width=img_w,
    #         #         #     # height=img_h,
    #         #         #     # image_file is your StringIO/BytesIO object
    #         #         #     file=ImageFile(img_file, name=img_name.decode("utf-8"), size=(img_w, img_h)),
    #         #         # )
    #         #         # print("SAVED IMAGE...")
    #
    #         post_type = post["post_type"]
    #         path = post["post_name"]
    #
    #         if not path:
    #             continue
    #
    #         content = post["content"] or "Test"
    #
    #         post_date = None
    #
    #         if "post_date" in post:
    #             post_date = datetime.strptime(
    #                 post["post_date"],
    #                 '%Y-%m-%d %H:%M:%S',
    #             )
    #
    #         if post_type == "page":
    #             parent_page = home_page
    #
    #             # print("legacy_guid", legacy_guid)
    #             # print(path)
    #             path = get_slug(path)
    #
    #             print(f"path={path}")
    #
    #             content_page = ContentPage(
    #                 #path=path,
    #                 title=title,
    #                 slug=slugify(path),
    #                 legacy_guid=legacy_guid,
    #                 legacy_content=content,
    #                 live=True,
    #                 first_published_at=post_date,
    #             )
    #             parent_page.add_child(instance=content_page)
    #             parent_page.save()
    #
    #         elif post_type == "news":
    #             create_news_page(
    #                 post,
    #                 home_page,
    #                 post_date,
    #                 path,
    #                 content,
    #                 title,
    #                 legacy_guid,
    #             )

        # content = php_loads(bytes(post["content"], encoding='utf-8'))
        #
        # print(content)
        #


