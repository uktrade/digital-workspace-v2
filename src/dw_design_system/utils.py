from datetime import datetime
from json import JSONDecoder, scanner

from django.core.paginator import Page, Paginator
from django.http import HttpRequest
from django.utils import timezone
from wagtail.images.models import Image

from news.models import NewsPage


DATETIME_STR = "datetime"
IMAGE_STR = "Image"
PAGINATOR_STR = "Paginator"
RANGE_STR = "Range"


def get_dwds_templates(template_type, request: HttpRequest):
    thumbnail_file = Image.objects.last()
    pages = Paginator(NewsPage.objects.all(), 2).page(1)

    dwds_templates = {
        "content": [
            {
                "name": "Content Header",
                "template": "dwds/elements/content_header.html",
                "context": {},
            },
            {
                "name": "Content Image",
                "template": "dwds/elements/content_image.html",
                "context": {
                    "content_image": thumbnail_file,
                },
            },
            {
                "name": "Content Main",
                "template": "dwds/elements/content_main.html",
                "context": {},
            },
            {
                "name": "Content Item",
                "template": "dwds/elements/content_item.html",
                "context": {},
            },
            {
                "name": "Content Item Card",
                "template": "dwds/layouts/content_item_card.html",
                "context": {"flippable":False},
            },
        ],
        "components": [
            {
                "name": "Action Link",
                "template": "dwds/components/link_action.html",
                "context": {
                    "link_text": "Action Link",
                    "link_url": "https://www.gov.uk",
                    "left": True,
                    "right": True,
                },
            },
            {
                "name": "Link navigate",
                "template": "dwds/components/link_navigate.html",
                "context": {
                    "previous_url": "https://www.gov.uk",
                    "previous_text": "Previous",
                    "next_url": "https://www.gov.uk",
                    "next_text": "Next",
                },
            },
            {
                "name": "Banner",
                "template": "dwds/components/banner.html",
                "context": {
                    "alert": False,
                    "link": "https://www.gov.uk",
                    "text": (
                        "This is a banner for GOV.UK, it can be really long or"
                        " really short. In this example we have a long banner to"
                        " show how it looks with a lot of text."
                    ),
                },
            },
            {
                "name": "CTA",
                "template": "dwds/components/cta.html",
                "context": {
                    "highlight": True,
                    "url": "https://www.gov.uk",
                    "title": "This is a CTA for GOV.UK",
                    "description": "This is a description for the CTA",
                },
            },
            {
                "name": "Link list",
                "template": "dwds/components/link_list.html",
                "context": {
                    "title": "Link List",
                    "description": "A list of links",
                    "list": [
                        {
                            "link": "https://www.gov.uk",
                            "text": f"Link {i + 1} for GOV.UK",
                        }
                        for i in range(10)
                    ],
                },
            },
            {
                "name": "Engagement",
                "template": "dwds/components/engagement.html",
                "context": {
                    "url": "https://www.gov.uk",
                    "title": "This is engaging content for GOV.UK with a really long title to show what a long title looks like",
                    "excerpt": "This is an excerpt for the engaging content. This excerpt is longer than it should be for test data.",
                    "author": "John Doe",
                    "date": timezone.now(),
                    "thumbnail": thumbnail_file,
                    "comment_count": 10,
                    "created_date": timezone.now(),
                    "updated_date": timezone.now(),
                },
            },
            {
                "name": "One Up",
                "template": "dwds/components/one_up.html",
                "context": {
                    "url": "https://www.gov.uk",
                    "title": "One Up",
                    "excerpt": "This is an excerpt for the one up content",
                    "date": timezone.now(),
                    "thumbnail": thumbnail_file,
                    "comment_count": 10,
                    "created_date": timezone.now(),
                    "updated_date": timezone.now(),
                },
            },
            {
                "name": "Promo Banner",
                "template": "dwds/components/promo.html",
                "context": {
                    "ribbon_text": "One DBT",
                    "description": "We value your ideas to help make it simpler to work at DBT, make a difference and celebrate innovation.",
                    "link_text": "Collaborate and connect",
                    "link_url": "http://localhost:8000/dwds/",
                    "background_image": thumbnail_file,
                },
            },
            {
                "name": "Pagination",
                "template": "dwds/components/pagination.html",
                "context": {"pages": pages, "request": request},
            },
            {
                "name": "Profile Info",
                "template": "dwds/components/profile_info.html",
                "context": {
                    "show_profile_image": True,
                    "name": "John Doe",
                    "title": "Permanent Secretary",
                    "profile_url": "https://www.gov.uk",
                    "profile_image_url": thumbnail_file.file.url,
                    "location": "London",
                    "show_icons": True,
                    "email_address": "someone@example.com",
                    "phone_number": "0123456789",
                },
            },
        ],
        "layouts": [],
    }
    return dwds_templates[template_type]


def to_json(val):
    if isinstance(val, datetime):
        return f"{DATETIME_STR} {val.isoformat()}"
    if isinstance(val, Image):
        return f"{IMAGE_STR} {val.pk}"
    if isinstance(val, Page):
        print("PAG Found")
        return f"{PAGINATOR_STR}"
    if isinstance(val, range):
        return f"{RANGE_STR} {val.start} {val.stop}"

    print(type(val))
    return val


def parse_str(val):
    if val.startswith(DATETIME_STR):
        return datetime.fromisoformat(val.split(" ")[1])
    if val.startswith(IMAGE_STR):
        return Image.objects.get(pk=int(val.split(" ")[1]))
    if val.startswith(PAGINATOR_STR):
        return Paginator(NewsPage.objects.all(), 2).page(1)
    if val.startswith(RANGE_STR):
        str_range = val.split(" ")
        return range(int(str_range[1]), int(str_range[2]))

    return val


class CustomJSONDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_string = parse_str
        self.scan_once = scanner.make_scanner(self)

    def decode(self, *args, **kwargs):
        obj = super().decode(*args, **kwargs)
        for k, v in obj.items():
            if isinstance(v, str):
                obj[k] = parse_str(v)
        return obj
