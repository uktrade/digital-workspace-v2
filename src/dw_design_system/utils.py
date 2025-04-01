from datetime import datetime
from json import JSONDecoder, scanner

from django.core import paginator
from django.http import HttpRequest
from django.utils import timezone
from wagtail.images.models import Image
from wagtail.models import Page

from content.models import ContentPage
from interactions.services import comments as comments_service
from news.models import Comment, NewsPage
from user.models import User


USER_STR = "user"
DATETIME_STR = "datetime"
IMAGE_STR = "Image"
PAGE_STR = "Page"
PAGINATOR_STR = "Paginator"
RANGE_STR = "Range"

ICON_CONTEXT = {
    "small": False,
    "dark": False,
    "hover_dark": True,
    "hover_light": False,
}


INTERNAL_URL = "/"
EXTERNAL_URL = "https://gov.uk/"


def get_page_that_has_comments() -> ContentPage | None:
    for p in ContentPage.objects.filter(comments__isnull=False):
        if p.comments.filter(is_visible=True).exists():
            return p
    return None


def get_dwds_templates(template_type, request: HttpRequest):
    user = request.user

    thumbnail_file = Image.objects.last()
    thumbnail_url = (
        thumbnail_file.file.url if thumbnail_file and thumbnail_file.file else None
    )
    page = NewsPage.objects.last()
    pages = paginator.Paginator(NewsPage.objects.all(), 2).page(1)

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
                "context": {"flippable": False},
            },
        ],
        "components": [
            {
                "name": "Action Link",
                "template": "dwds/components/link_action.html",
                "context": {
                    "link_text": "Action Link",
                    "link_url": INTERNAL_URL,
                    "left": True,
                    "right": True,
                },
            },
            {
                "name": "Link navigate",
                "template": "dwds/components/link_navigate.html",
                "context": {
                    "previous_url": INTERNAL_URL,
                    "previous_text": "Previous",
                    "next_url": INTERNAL_URL,
                    "next_text": "Next",
                },
            },
            {
                "name": "Banner",
                "template": "dwds/components/banner.html",
                "context": {
                    "alert": False,
                    "link": INTERNAL_URL,
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
                    "highlight": False,
                    "url": INTERNAL_URL,
                    "title": "This is a CTA for GOV.UK",
                    "description": "This is a description for the CTA",
                    "footer_text": "This is some footer text",
                },
            },
            {
                "name": "CTA Button",
                "template": "dwds/components/cta_button.html",
                "context": {
                    "icon": "dwds/icons/feedback.html",
                    "url": INTERNAL_URL,
                    "title": "This is a CTA for GOV.UK",
                    "description": "This is a description for the CTA",
                    "footer_text": "This is some footer text",
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
                            "link": EXTERNAL_URL,
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
                    "url": INTERNAL_URL,
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
                "name": "Quotes Component",
                "template": "dwds/components/quote.html",
                "context": {
                    "highlight": True,
                    "quote": "It makes you happy that you provided several kilowatts to the power sector, and it means that someone will turn their lights on today. That motivates me, that’s your work really impacts the wellbeing of the country.",
                    "source_name": "Pavolo Sorokin",
                    "source_url": "https://www.gov.uk",
                    "source_image": thumbnail_url,
                    "source_role": "Trade policy and Healthcare Adviser",
                    "source_team": "Ukraine",
                    "source_team_url": "https://www.gov.uk",
                },
            },
            {
                "name": "Image with text Component",
                "template": "dwds/components/image_with_text.html",
                "context": {
                    "heading": "Heading for the component",
                    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                    "image_position": "right",
                    "image": thumbnail_file,
                    "image_description": "Text for image description",
                    "alt": "Alt text for screen readers",
                },
            },
            {
                "name": "Spotlight",
                "template": "dwds/components/spotlight.html",
                "context": {
                    "url": INTERNAL_URL,
                    "title": "Speak Up Week 2025",
                    "excerpt": "At DBT, we want everyone to feel respected, included and empowered to speak up if something doesn't feel right",
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
                    "url": INTERNAL_URL,
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
                    "link_url": INTERNAL_URL,
                    "background_image": thumbnail_file,
                },
            },
            {
                "name": "Message",
                "template": "dwds/components/message.html",
                "context": {
                    "title": "Message title",
                    "body": "This is the message body with some content in it.",
                },
            },
            {
                "name": "Menu (vertical)",
                "template": "dwds/components/menu_vertical.html",
                "context": {
                    "current_page": page,
                    "enable_current_page_menu": True,
                    "items": [
                        {
                            "active": False,
                            "title": f"Menu item {i + 1}",
                            "url": INTERNAL_URL,
                        }
                        for i in range(10)
                    ],
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
                    "profile_url": INTERNAL_URL,
                    "profile_image_url": thumbnail_url,
                    "location": "London",
                    "show_icons": True,
                    "email_address": "someone@example.com",
                    "phone_number": "0123456789",
                },
            },
            {
                "name": "Accordion",
                "template": "dwds/components/accordion.html",
                "context": {
                    "items": [
                        {
                            "heading": "Understanding agile project management",
                            "summary": "Introductions, methods, core features.",
                            "content": "This is the content for agile project management.",
                        },
                        {
                            "heading": "Working with agile methods",
                            "summary": "Workspaces, tools and techniques, user stories, planning.",
                            "content": "This is the content for agile methods.",
                        },
                        {
                            "heading": "Governing agile services",
                            "summary": "Principles, measuring progress, spending money.",
                            "content": "This is the content for agile services.",
                        },
                        {
                            "heading": "Phases of an agile project",
                            "summary": "Discovery, alpha, beta, live and retirement.",
                            "content": "This is the content for agile project.",
                        },
                    ]
                },
            },
            {
                "name": "Details",
                "template": "dwds/components/details.html",
                "context": {
                    "summary_text": "This is a details component",
                    "content": "This is some content that is hidden by default",
                },
            },
            {
                "name": "Copy Text",
                "template": "dwds/components/copy_text.html",
                "context": {
                    "text": EXTERNAL_URL,
                    "hide_input": False,
                },
            },
            {
                "name": "Modal",
                "template": "dwds/components/modal.html",
                "context": {
                    "content": "MODAL CONTENT",
                },
            },
            {
                "name": "Toggle Visibility",
                "template": "dwds/components/toggle_visibility_button.html",
                "context": {},
            },
            {
                "name": "Author",
                "template": "dwds/components/author.html",
                "context": {
                    "name": "John Doe",
                    "profile_image_url": thumbnail_url,
                    "profile_url": INTERNAL_URL,
                    "published_timestamp": timezone.now(),
                    "updated_timestamp": timezone.now(),
                },
            },
            {
                "name": "Comment",
                "template": "dwds/components/comment.html",
                "context": {
                    "user": user,
                    "comment": comments_service.comment_to_dict(Comment.objects.last()),
                },
            },
            {
                "name": "Comments",
                "template": "dwds/components/comments.html",
                "context": {
                    "user": user,
                    "comment_count": 5,
                    "comments": [
                        comments_service.comment_to_dict(comment)
                        for comment in comments_service.get_page_comments(
                            page=get_page_that_has_comments()
                        )
                    ],
                },
            },
            {
                "name": "Link External",
                "template": "dwds/components/link_external.html",
                "context": {},
            },
        ],
        "icons": [
            {
                "name": "Arrow Blue Background",
                "template": "dwds/icons/arrow-blue-bg.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Arrow Left",
                "template": "dwds/icons/arrow-left.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Arrow Right",
                "template": "dwds/icons/arrow-right.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Briefcase",
                "template": "dwds/icons/briefcase.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Email",
                "template": "dwds/icons/email.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Marker",
                "template": "dwds/icons/marker.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Phone",
                "template": "dwds/icons/phone.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Bookmark",
                "template": "dwds/icons/bookmark.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Celebrate",
                "template": "dwds/icons/celebrate.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Comment",
                "template": "dwds/icons/comment.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Dislike",
                "template": "dwds/icons/dislike.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Feedback",
                "template": "dwds/icons/feedback.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Like",
                "template": "dwds/icons/like.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Love",
                "template": "dwds/icons/love.html",
                "context": ICON_CONTEXT,
            },
            {
                "name": "Unhappy",
                "template": "dwds/icons/unhappy.html",
                "context": ICON_CONTEXT,
            },
        ],
        "layouts": [],
    }
    return dwds_templates[template_type]


def to_json(val):
    if isinstance(val, User):
        return f"{USER_STR} {val.pk}"
    if isinstance(val, datetime):
        return f"{DATETIME_STR} {val.isoformat()}"
    if isinstance(val, Image):
        return f"{IMAGE_STR} {val.pk}"
    if isinstance(val, paginator.Page):
        return f"{PAGINATOR_STR}"
    if isinstance(val, Page):
        return f"{PAGE_STR} {val.pk}"
    if isinstance(val, range):
        return f"{RANGE_STR} {val.start} {val.stop}"

    return val


def parse_str(val):
    if val.startswith(USER_STR):
        return User.objects.get(pk=int(val.split(" ")[1]))
    if val.startswith(DATETIME_STR):
        return datetime.fromisoformat(val.split(" ")[1])
    if val.startswith(IMAGE_STR):
        return Image.objects.get(pk=int(val.split(" ")[1]))
    if val.startswith(PAGE_STR):
        return Page.objects.get(pk=int(val.split(" ")[1]))
    if val.startswith(PAGINATOR_STR):
        return paginator.Paginator(NewsPage.objects.all(), 2).page(1)
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
                obj[k] = self.parse_string(v)
        return obj
