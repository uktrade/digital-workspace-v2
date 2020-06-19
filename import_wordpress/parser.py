import os

import wpparser

from django.conf import settings
from django.template.defaultfilters import slugify

from phpserialize import loads as php_loads

from wagtail.core.models import Page

from content.models import HTMLPage

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

home_page = Page.objects.filter(slug="home").first()

for post in wp_data["posts"]:
    title = post["title"]
    path = post["link"]
    #published = post["pubDate"]

    if "post_type" in post:
        post_type = post["post_type"]

        content = post["content"] or "Test"

        if post_type == "page":
            html_page = HTMLPage(
                #path=path,
                title=title,
                slug=slugify(title),
                body=content,
            )
            home_page.add_child(instance=html_page)
            home_page.save()

            print(html_page)
            print(f"created {path}")

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
