from datetime import datetime
from json import JSONDecoder, scanner

from django.core.paginator import Paginator
from django.utils import timezone
from wagtail.images.models import Image

from home.templatetags.cards import pages_to_cards
from news.models import NewsPage


DATETIME_STR = "datetime"
IMAGE_STR = "Image"


def get_components():
    thumbnail_file = Image.objects.first()
    pages = Paginator(NewsPage.objects.all(), 2).page(1)
    return [
        {
            "name": "Card",
            "template": "dwds/elements/extendable/card.html",
            "context": {},
        },
        {
            "name": "Banner Card",
            "template": "dwds/components/banner_card.html",
            "context": {
                "alert": False,
                "link": "https://www.gov.uk",
                "text": "This is a banner card for GOV.UK",
            },
        },
        {
            "name": "CTA Card",
            "template": "dwds/components/cta_card.html",
            "context": {
                "link": "https://www.gov.uk",
                "title": "This is a CTA card for GOV.UK",
                "description": "This is a description for the CTA card",
            },
        },
        {
            "name": "Engagement Card",
            "template": "dwds/components/engagement_card.html",
            "context": {
                "url": "https://www.gov.uk",
                "title": "This is an engagement card for GOV.UK",
                "excerpt": "This is an excerpt for the engagement card",
                "author": "John Doe",
                "date": timezone.now(),
                "thumbnail": thumbnail_file,
            },
        },
        {
            "name": "Card Group",
            "template": "dwds/components/card_group.html",
            "context": {
                "card_group_title": "Latest DBT news",
                "cards": pages_to_cards(
                    NewsPage.objects.all().annotate_with_comment_count()[:3]
                ),
                "footer_link": "/news-and-views/",
                "footer_link_text": "View all news",
                "show_hr": True,
            },
        },
        {
            "name": "Link List",
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
            "name": "Navigation Card",
            "template": "dwds/components/navigation_card.html",
            "context": {
                "url": "https://www.gov.uk",
                "title": "Navigation Card",
                "summary": "This is a summary for the navigation card",
            },
        },
        {
            "name": "One Up Card",
            "template": "dwds/components/one_up_card.html",
            "context": {
                "url": "https://www.gov.uk",
                "title": "One Up Card",
                "excerpt": "This is an excerpt for the one up card",
                "date": timezone.now(),
                "thumbnail": thumbnail_file,
            },
        },
        {
            "name": "Pagination",
            "template": "dwds/components/pagination.html",
            "context": {"pages": pages, "pagination_range": range(1, 11)},
        },
        {
            "name": "Link navigation",
            "template": "dwds/components/link_navigate.html",
            "context": {
                "previous_url": "https://www.gov.uk",
                "previous_text": "Previous",
                "next_url": "https://www.gov.uk",
                "next_text": "Next",
            },
        },
    ]


def to_json(val):
    if isinstance(val, datetime):
        return f"{DATETIME_STR} {val.isoformat()}"
    if isinstance(val, Image):
        return f"{IMAGE_STR} {val.pk}"
    return val


def parse_str(val):
    if " " not in val:
        return val

    if val.startswith(DATETIME_STR):
        return datetime.fromisoformat(val.split(" ")[1])
    if val.startswith(IMAGE_STR):
        return Image.objects.get(pk=int(val.split(" ")[1]))

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
