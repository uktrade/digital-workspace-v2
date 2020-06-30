import os

from datetime import datetime

import wpparser

from django.conf import settings
from django.core.files.images import ImageFile
from django.template.defaultfilters import slugify

from urllib.request import urlopen
from urllib.parse import urlparse
from io import BytesIO
from django.core.files.images import ImageFile

from phpserialize import loads as php_loads

from wagtail.core.models import Page
from wagtail.images.models import Image

from content.models import ContentPage, NewsHome, NewsPage

xml_file = os.path.join(settings.BASE_DIR, "wordpress.xml")
wp_data = wpparser.parse(xml_file)

import io


#dict_to_list()

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

img_extensions = [".jpg", ".png", ".gif", ".webp"]


def get_slug(slug):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-1")

    return slug


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


def parse_xml_file():
    home_page = Page.objects.filter(slug="home").first()

    print("home_page", home_page)

    for post in wp_data["posts"]:

        title = "Placeholder..."

        if "title" in post and post["title"] not in (None, ""):
            title = post["title"]

        legacy_guid = post["guid"]

        if "post_type" in post:
            # Images
            if post["post_type"] == "attachment":
                if is_image(post):
                    img_name, img_url, img_w, img_h = get_image_properties(post)
                    #img_file = BytesIO(urlopen(img_url).read())

                    import requests


                    http_res = requests.get(img_url)
                    image_file = ImageFile(BytesIO(http_res.content), name=img_name.decode("utf-8"))
                    image = Image(title=title, file=image_file, width=1, height=1)
                    image.save()



                    print("img_name", img_name.decode("utf-8") )
                    print("img_url", img_url)
                    print("img_w", img_w)
                    print("img_h", img_h)
                    #
                    # Image.objects.create(
                    #     title="Image title",
                    #     # width=img_w,
                    #     # height=img_h,
                    #     # image_file is your StringIO/BytesIO object
                    #     file=ImageFile(img_file, name=img_name.decode("utf-8"), size=(img_w, img_h)),
                    # )
                    # print("SAVED IMAGE...")

            post_type = post["post_type"]
            path = post["post_name"]

            if not path:
                continue

            content = post["content"] or "Test"

            post_date = None

            if "post_date" in post:
                post_date = datetime.strptime(
                    post["post_date"],
                    '%Y-%m-%d %H:%M:%S',
                )

            if post_type == "page":
                parent_page = home_page

                # print("legacy_guid", legacy_guid)
                # print(path)
                path = get_slug(path)

                print(f"path={path}")

                content_page = ContentPage(
                    #path=path,
                    title=title,
                    slug=slugify(path),
                    legacy_guid=legacy_guid,
                    legacy_content=content,
                    live=True,
                    first_published_at=post_date,
                )
                parent_page.add_child(instance=content_page)
                parent_page.save()

            elif post_type == "news":
                # check for existence of parent news page
                news_home = Page.objects.filter(slug="news-and-views").first()

                print("news_home", news_home)

                if not news_home:
                    news_home = NewsHome(
                        #path="news-and-views",
                        title="All News",
                        slug="news-and-views",
                        live=True,
                        first_published_at=post_date,
                    )

                    home_page.add_child(instance=news_home)
                    home_page.save()

                news_home = NewsHome.objects.all().first()

                path = get_slug(path)

                print(f"path={path}")

                content_page = NewsPage(
                    #path=path,
                    title=title,
                    slug=slugify(path),
                    legacy_guid=legacy_guid,
                    legacy_content=content,
                    live=True,
                )
                news_home.add_child(instance=content_page)
                news_home.save()

        # content = php_loads(bytes(post["content"], encoding='utf-8'))
        #
        # print(content)
        #
        # # content_page = ContentPage(
        # #
        # # )
        # # content_page.save()
        # if counter > 20:
        #     break  # Break until we have established logic
        #
        # print("=====")
        # counter += 1

    print(post_types)
